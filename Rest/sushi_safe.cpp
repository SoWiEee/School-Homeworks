// g++ -std=c++17 -O3 -pthread sushi_safe.cpp -o sushi.exe -fexec-charset=big5
// ./sushi path/to/test.csv

#include <algorithm>
#include <atomic>
#include <condition_variable>
#include <cctype>
#include <deque>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <memory>
#include <mutex>
#include <optional>
#include <queue>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

using namespace std;

// ============================================================
// 0) Parsing utils
// ============================================================
enum class CustomerType { INDIVIDUAL, FAMILY, WITH_BABY, WHEELCHAIR, UNKNOWN };

static string trim(const string& s) {
    size_t b = 0, e = s.size();
    while (b < e && isspace((unsigned char)s[b])) b++;
    while (e > b && isspace((unsigned char)s[e - 1])) e--;
    return s.substr(b, e - b);
}
static string upper(string s) {
    for (auto& ch : s) ch = (char)toupper((unsigned char)ch);
    return s;
}
static CustomerType parseType(const string& raw) {
    string s = upper(trim(raw));
    if (s == "INDIVIDUAL") return CustomerType::INDIVIDUAL;
    if (s == "FAMILY") return CustomerType::FAMILY;
    if (s == "WITH_BABY") return CustomerType::WITH_BABY;
    if (s == "WHEELCHAIR" || s == "WHEELCHAALIR") return CustomerType::WHEELCHAIR;
    return CustomerType::UNKNOWN;
}
static string typeLabel(CustomerType t) {
    switch (t) {
        case CustomerType::INDIVIDUAL: return "INDIVIDUAL";
        case CustomerType::FAMILY: return "FAMILY";
        case CustomerType::WITH_BABY: return "WITH_BABY";
        case CustomerType::WHEELCHAIR: return "WHEELCHAIR";
        default: return "UNKNOWN";
    }
}
static vector<string> splitCSVLine(const string& line) {
    vector<string> out;
    string cur;
    bool inQuote = false;
    for (char ch : line) {
        if (ch == '"') inQuote = !inQuote;
        else if (ch == ',' && !inQuote) { out.push_back(trim(cur)); cur.clear(); }
        else cur.push_back(ch);
    }
    out.push_back(trim(cur));
    return out;
}
static bool isHeaderRow(const vector<string>& cols) {
    if (cols.empty()) return true;
    string s0 = trim(cols[0]);
    if (s0.empty()) return true;
    bool allDigits = true;
    for (char c : s0) allDigits = allDigits && (isdigit((unsigned char)c) || c=='-' || c=='+');
    return !allDigits;
}

// numeric-ish thread id
static long long thread_id_num() {
    static std::hash<std::thread::id> H;
    return (long long)(H(std::this_thread::get_id()) % 1000000);
}

// ============================================================
// 1) Model
// ============================================================
struct Customer {
    int ID{};
    int ArrivalTime{};     // -1 means preloaded
    CustomerType Type{};
    int PartySize{};
    int BabyNeed{};
    int WheelNeed{};
    int DiningTime{};

    bool arrived = false;
    bool seated  = false;
    bool waitedLogged = false;

    int seatTime  = -1;
    int leaveTime = -1;

    // actual consumed resources (IMPORTANT: use what we really used)
    int usedBaby  = 0;
    int usedWheel = 0;

    vector<string> seatIDs;
};

// ============================================================
// 2) Seats / Plans
// ============================================================
enum class PlanKind { Singles, Sofa4, Sofa6 };

struct SeatPlan {
    bool ok = false;
    PlanKind kind{};
    vector<int> singleIdx;
    int sofaIdx = -1;

    int babyUse  = 0;
    int wheelUse = 0;

    vector<string> seatIDs;
};

static string fmtID(const string& prefix, int idx1based, int width) {
    ostringstream oss;
    oss << prefix << setw(width) << setfill('0') << idx1based;
    return oss.str();
}
static string joinIDsCSV(const vector<string>& ids) {
    string out;
    for (size_t i = 0; i < ids.size(); i++) {
        if (i) out += ",";
        out += ids[i];
    }
    return out;
}

// ============================================================
// 3) Simulator: only worker threads mutate shared state
// ============================================================
class SushiBarSimSafe {
public:
    SushiBarSimSafe(int singles=20, int four=8, int six=5, int baby=4, int wheel=2,
                    int numWaiters=3, int maxSkips=3)
        : totalBaby_(baby),
          totalWheel_(wheel),
          availBaby_(baby),
          availWheel_(wheel),
          seatsSingle_(singles, 0),
          sofas4_(four, 0),
          sofas6_(six, 0),
          accessible4_(0),
          accessible6_(0),
          numWaiters_(numWaiters),
          maxSkips_(maxSkips)
    {}

    vector<Customer> readCSV(const string& path) {
        ifstream fin(path);
        if (!fin) throw runtime_error("cannot open csv: " + path);

        vector<Customer> out;
        string line;
        bool first = true;
        while (getline(fin, line)) {
            line = trim(line);
            if (line.empty()) continue;
            auto cols = splitCSVLine(line);
            if (first) {
                first = false;
                if (isHeaderRow(cols)) continue;
            }
            if (cols.size() < 7) throw runtime_error("csv row needs 7 columns: " + line);

            Customer c;
            c.ID          = stoi(cols[0]);
            c.ArrivalTime = stoi(cols[1]);
            c.Type        = parseType(cols[2]);
            c.PartySize   = stoi(cols[3]);
            c.BabyNeed    = stoi(cols[4]);
            c.WheelNeed   = stoi(cols[5]);
            c.DiningTime  = stoi(cols[6]);
            out.push_back(c);
        }
        return out;
    }

    void loadCustomers(const vector<Customer>& rows) {
        lock_guard<mutex> lk(mu_);

        initial_.clear();
        incoming_.clear();
        arrivalsByTime_.clear();
        releasesByTime_.clear();
        waitingQ_.clear();
        arrivedThisTime_.clear();
        taskQ_.clear();
        while (!timeHeap_.empty()) timeHeap_.pop();

        // reset resources / seats
        availBaby_  = totalBaby_;
        availWheel_ = totalWheel_;
        fill(seatsSingle_.begin(), seatsSingle_.end(), 0);
        fill(sofas4_.begin(),      sofas4_.end(),      0);
        fill(sofas6_.begin(),      sofas6_.end(),      0);

        int tempID = -1;
        for (auto r : rows) {
            auto c = make_shared<Customer>(r);
            if (c->ID == -1) c->ID = tempID--;
            if (c->ArrivalTime == -1) initial_.push_back(c);
            else incoming_.push_back(c);
        }

        stable_sort(incoming_.begin(), incoming_.end(),
            [](const auto& a, const auto& b){
                if (a->ArrivalTime != b->ArrivalTime) return a->ArrivalTime < b->ArrivalTime;
                return a->ID < b->ID;
            });

        for (auto& c : incoming_) {
            arrivalsByTime_[c->ArrivalTime].push_back(c);
            timeHeap_.push(c->ArrivalTime);
        }

        // init time
        T_ = 0;
        stopAll_ = false;
        activeWorkers_ = 0;
        waitedPrintedAtTime_ = -1;

        // preload-seat tasks at T=0
        for (auto& c : initial_) taskQ_.push_back(Task{TaskType::PRELOAD_SEAT, c});

        // arrivals at time 0 -> tasks now
        if (auto it0 = arrivalsByTime_.find(0); it0 != arrivalsByTime_.end()) {
            for (auto& c : it0->second) taskQ_.push_back(Task{TaskType::ARRIVAL, c});
            arrivalsByTime_.erase(it0);
        }
    }

    void runAll() {
        startWaiters();
        startClock();

        if (clockThread_.joinable()) clockThread_.join();
        for (auto& th : waiterThreads_) if (th.joinable()) th.join();
        waiterThreads_.clear();
    }

private:
    // -----------------------------
    // Tasks: RELEASE > PRELOAD_SEAT > ARRIVAL
    // -----------------------------
    enum class TaskType { RELEASE, PRELOAD_SEAT, ARRIVAL };
    struct Task {
        TaskType type;
        shared_ptr<Customer> c;
    };

    struct QueuedCustomer {
        shared_ptr<Customer> c;
        int skip_count = 0; // head can be skipped up to maxSkips_
    };

    mutex mu_;
    condition_variable cvWork_;
    condition_variable cvClock_;

    int  T_ = 0;
    bool stopAll_ = false;

    int activeWorkers_ = 0;
    int waitedPrintedAtTime_ = -1;

    thread clockThread_;
    vector<thread> waiterThreads_;

    const int totalBaby_;
    const int totalWheel_;
    int availBaby_;
    int availWheel_;

    vector<int> seatsSingle_;
    vector<int> sofas4_;
    vector<int> sofas6_;
    int accessible4_;
    int accessible6_;

    int numWaiters_;
    int maxSkips_;

    // ===== debug =====
    bool debug_ = false; //可以設 false

    vector<shared_ptr<Customer>> initial_;
    vector<shared_ptr<Customer>> incoming_;

    deque<QueuedCustomer> waitingQ_;

    map<int, vector<shared_ptr<Customer>>> arrivalsByTime_;
    map<int, vector<shared_ptr<Customer>>> releasesByTime_;

    priority_queue<int, vector<int>, greater<int>> timeHeap_;
    deque<Task> taskQ_;

    vector<shared_ptr<Customer>> arrivedThisTime_;

private:
    // -----------------------------
    // Constraints & counting
    // -----------------------------
    bool everSatisfiableLocked(const Customer& c) const {
        if (c.PartySize < 1 || c.PartySize > 6) return false;
        if (c.BabyNeed < 0 || c.WheelNeed < 0) return false;
        if (c.BabyNeed > totalBaby_) return false;
        if (c.WheelNeed > totalWheel_) return false;
        if (c.Type == CustomerType::UNKNOWN) return false;
        if (c.DiningTime < 0) return false;
        return true;
    }

    int countFreeSinglesLocked() const { int cnt=0; for (int x: seatsSingle_) if (x==0) cnt++; return cnt; }
    int countFree4Locked() const { int cnt=0; for (int x: sofas4_) if (x==0) cnt++; return cnt; }
    int countFree6Locked() const { int cnt=0; for (int x: sofas6_) if (x==0) cnt++; return cnt; }

    bool anyOccupiedLocked() const {
        for (int x: seatsSingle_) if (x!=0) return true;
        for (int x: sofas4_) if (x!=0) return true;
        for (int x: sofas6_) if (x!=0) return true;
        return false;
    }

    optional<vector<int>> findConsecutiveSinglesLocked(int need) const {
        if (need <= 0 || need > (int)seatsSingle_.size()) return nullopt;
        int cnt = 0, start = -1;
        for (int i=0; i<(int)seatsSingle_.size(); i++) {
            if (seatsSingle_[i] == 0) {
                if (cnt==0) start=i;
                cnt++;
                if (cnt==need) {
                    vector<int> idx;
                    for (int j=0; j<need; j++) idx.push_back(start+j);
                    return idx;
                }
            } else {
                cnt=0;
            }
        }
        return nullopt;
    }

    optional<int> findFreeSofaLocked(const vector<int>& sofas, int begin, int endExclusive) const {
        for (int i=begin; i<endExclusive; i++) if (sofas[i]==0) return i;
        return nullopt;
    }

    optional<SeatPlan> makePlanLocked(const Customer& c) const {
        if (c.BabyNeed > availBaby_) return nullopt;

        // [!] 如果家庭有 baby 的話會被丟到吧檯 (is_baby = true)
        // const bool is_baby  = (c.BabyNeed > 0) || (c.Type == CustomerType::WITH_BABY);
        const bool is_baby  = (c.Type == CustomerType::WITH_BABY);
        const bool is_wheel = (c.WheelNeed > 0) || (c.Type == CustomerType::WHEELCHAIR);

        SeatPlan plan;

        // Baby chairs always counted if requested
        plan.babyUse = c.BabyNeed;

        // Wheelchair consumption rule:
        // - if wheelchair customer => at least 1 wheelchair resource
        // - else => consume c.WheelNeed (normally 0)
        int wheelConsume = 0;
        if (is_wheel) wheelConsume = max(1, c.WheelNeed);
        else wheelConsume = c.WheelNeed;

        if (wheelConsume > availWheel_) return nullopt;
        plan.wheelUse = wheelConsume;

        // WITH_BABY => consecutive singles only
        if (is_baby) {
            auto idxs = findConsecutiveSinglesLocked(c.PartySize);
            if (!idxs) return nullopt;
            plan.ok = true;
            plan.kind = PlanKind::Singles;
            plan.singleIdx = *idxs;
            for (int i : plan.singleIdx) plan.seatIDs.push_back(fmtID("S", i+1, 2));
            return plan;
        }

        // WHEELCHAIR => accessible sofa only (index 0)
        // WHEELCHAIR seating rule (NEW):
        // - group 1~4: prefer accessible 4P (4P01). If not available, may use accessible 6P (6P01).
        // - group 5~6: ONLY accessible 6P (6P01).
        if (is_wheel) {
            // group 5~6 -> only 6P accessible
            if (c.PartySize >= 5) {
                if (sofas6_[accessible6_] != 0) return nullopt;
                plan.ok = true;
                plan.kind = PlanKind::Sofa6;
                plan.sofaIdx = accessible6_;
                plan.seatIDs = { fmtID("6P", accessible6_+1, 2) };
                return plan;
            }

            // group 1~4 -> try 4P accessible first
            if (sofas4_[accessible4_] == 0) {
                plan.ok = true;
                plan.kind = PlanKind::Sofa4;
                plan.sofaIdx = accessible4_;
                plan.seatIDs = { fmtID("4P", accessible4_+1, 2) };
                return plan;
            }

            // fallback to 6P accessible
            if (sofas6_[accessible6_] == 0) {
                plan.ok = true;
                plan.kind = PlanKind::Sofa6;
                plan.sofaIdx = accessible6_;
                plan.seatIDs = { fmtID("6P", accessible6_+1, 2) };
                return plan;
            }

            return nullopt;
        }


        // INDIVIDUAL => any single seat
        if (c.Type == CustomerType::INDIVIDUAL && c.PartySize == 1) {
            for (int i=0; i<(int)seatsSingle_.size(); i++) {
                if (seatsSingle_[i] == 0) {
                    plan.ok = true;
                    plan.kind = PlanKind::Singles;
                    plan.singleIdx = {i};
                    plan.seatIDs = { fmtID("S", i+1, 2) };
                    return plan;
                }
            }
            return nullopt;
        }

        // FAMILY => normal sofa -> accessible sofa -> downgrade consecutive singles
        if (c.Type == CustomerType::FAMILY) {
            if (c.PartySize <= 4) {
                if (auto idx = findFreeSofaLocked(sofas4_, 1, (int)sofas4_.size())) {
                    plan.ok = true; plan.kind = PlanKind::Sofa4; plan.sofaIdx = *idx;
                    plan.seatIDs = { fmtID("4P", *idx+1, 2) };
                    return plan;
                }
            }
            if (c.PartySize <= 6) {
                if (auto idx = findFreeSofaLocked(sofas6_, 1, (int)sofas6_.size())) {
                    plan.ok = true; plan.kind = PlanKind::Sofa6; plan.sofaIdx = *idx;
                    plan.seatIDs = { fmtID("6P", *idx+1, 2) };
                    return plan;
                }
            }

            if (c.PartySize <= 4 && sofas4_[accessible4_] == 0) {
                plan.ok = true; plan.kind = PlanKind::Sofa4; plan.sofaIdx = accessible4_;
                plan.seatIDs = { fmtID("4P", accessible4_+1, 2) };
                return plan;
            }
            if (c.PartySize <= 6 && sofas6_[accessible6_] == 0) {
                plan.ok = true; plan.kind = PlanKind::Sofa6; plan.sofaIdx = accessible6_;
                plan.seatIDs = { fmtID("6P", accessible6_+1, 2) };
                return plan;
            }

            if (auto idxs = findConsecutiveSinglesLocked(c.PartySize)) {
                plan.ok = true;
                plan.kind = PlanKind::Singles;
                plan.singleIdx = *idxs;
                for (int i : plan.singleIdx) plan.seatIDs.push_back(fmtID("S", i+1, 2));
                return plan;
            }
            return nullopt;
        }

        return nullopt;
    }

    void applyPlanLocked(Customer& c, const SeatPlan& plan) {
        availBaby_  -= plan.babyUse;
        availWheel_ -= plan.wheelUse;

        if (plan.kind == PlanKind::Singles) {
            for (int idx : plan.singleIdx) seatsSingle_[idx] = c.ID;
        } else if (plan.kind == PlanKind::Sofa4) {
            sofas4_[plan.sofaIdx] = c.ID;
        } else {
            sofas6_[plan.sofaIdx] = c.ID;
        }

        c.seated   = true;
        c.seatTime = T_;
        c.seatIDs  = plan.seatIDs;

        c.usedBaby  = plan.babyUse;
        c.usedWheel = plan.wheelUse;

        c.leaveTime = c.seatTime + c.DiningTime;
    }

    void releaseLocked(Customer& c) {
        // return what we actually used
        availBaby_  += c.usedBaby;
        availWheel_ += c.usedWheel;

        for (const auto& id : c.seatIDs) {
            if (!id.empty() && id[0] == 'S') {
                int idx = stoi(id.substr(1));
                if (1 <= idx && idx <= (int)seatsSingle_.size()) seatsSingle_[idx-1] = 0;
            } else if (id.rfind("4P", 0) == 0) {
                int idx = stoi(id.substr(2));
                if (1 <= idx && idx <= (int)sofas4_.size()) sofas4_[idx-1] = 0;
            } else if (id.rfind("6P", 0) == 0) {
                int idx = stoi(id.substr(2));
                if (1 <= idx && idx <= (int)sofas6_.size()) sofas6_[idx-1] = 0;
            }
        }
    }

    void scheduleReleaseLocked(const shared_ptr<Customer>& c) {
        if (!c || !c->seated) return;
        int lt = c->leaveTime;
        if (lt < 0) return;

        if (lt == T_) {
            taskQ_.push_back(Task{TaskType::RELEASE, c});
            return;
        }
        releasesByTime_[lt].push_back(c);
        timeHeap_.push(lt);
    }

    // -----------------------------
    // Logging
    // -----------------------------
    string demandStringLocked(const Customer& c) const {
        vector<string> parts;

        // [!] 如果家庭有 baby 的話會印出單人座 (is_baby = true)
        // const bool is_baby  = (c.BabyNeed > 0) || (c.Type == CustomerType::WITH_BABY);
        const bool is_baby  = (c.Type == CustomerType::WITH_BABY);
        const bool is_wheel = (c.WheelNeed > 0) || (c.Type == CustomerType::WHEELCHAIR);

        if (is_wheel) {
            if (c.PartySize <= 4) {
                parts.push_back("1 accessible_sofa (prefer 4P, fallback 6P)");
            } else {
                parts.push_back("1 accessible_sofa (6P only)");
            }
            parts.push_back(to_string(max(1, c.WheelNeed)) + " wheelchair");
            if (c.BabyNeed > 0) parts.push_back(to_string(c.BabyNeed) + " baby_chair");
        }
        else if (is_baby) {
            parts.push_back(to_string(c.PartySize) + " single_seats");
            parts.push_back(to_string(c.BabyNeed) + " baby_chair");
            if (c.WheelNeed > 0) parts.push_back(to_string(c.WheelNeed) + " wheelchair");
        } else if (c.Type == CustomerType::INDIVIDUAL && c.PartySize == 1) {
            parts.push_back("1 single_seat");
        } else { // FAMILY
            parts.push_back((c.PartySize <= 4) ? "1 four_seat_sofa" : "1 six_seat_sofa");
            if (c.BabyNeed > 0) parts.push_back(to_string(c.BabyNeed) + " baby_chair");
            if (c.WheelNeed > 0) parts.push_back(to_string(c.WheelNeed) + " wheelchair");
        }

        string out;
        for (size_t i=0; i<parts.size(); i++) { if (i) out += ", "; out += parts[i]; }
        return out;
    }

    void logLineLocked(long long tid, const Customer& c, const string& action) {
        ostringstream oss;
        oss << "[" << tid << "] "
            << "[" << T_ << "] "
            << "[" << typeLabel(c.Type) << "] "
            << "ID: " << c.ID
            << " | 需求: " << demandStringLocked(c)
            << " | " << action;

        if ((action == "seated" || action == "release") && !c.seatIDs.empty()) {
            oss << ", id:[" << joinIDsCSV(c.seatIDs) << "]";
        }

        oss << " | 剩餘資源: "
            << "S=" << countFreeSinglesLocked()
            << ", 4P=" << countFree4Locked()
            << ", 6P=" << countFree6Locked()
            << ", B=" << availBaby_
            << ", W=" << availWheel_;

        cout << oss.str() << "\n";
        cout.flush();
    }

    void logDebugLocked(long long tid, const string& msg) {
        if (!debug_) return;
        ostringstream oss;
        oss << "[" << tid << "] "
            << "[" << T_ << "] "
            << "[DEBUG] " << msg
            << " | Q=" << waitingQ_.size()
            << " | S=" << countFreeSinglesLocked()
            << ",4P=" << countFree4Locked()
            << ",6P=" << countFree6Locked()
            << ",B=" << availBaby_
            << ",W=" << availWheel_;
        cout << oss.str() << "\n";
        cout.flush();
    }

    void logWaitedOncePerTimeLocked(long long tid) {
        if (waitedPrintedAtTime_ == T_) return;
        waitedPrintedAtTime_ = T_;

        for (auto& c : arrivedThisTime_) {
            if (!c) continue;
            if (c->seated) continue;
            if (c->waitedLogged) continue;
            c->waitedLogged = true;
            logLineLocked(tid, *c, "waited");
        }
    }

    // -----------------------------
    // Task priority pop
    // -----------------------------
    static int pri(TaskType t) {
        if (t == TaskType::RELEASE) return 0;
        if (t == TaskType::PRELOAD_SEAT) return 1;
        return 2;
    }

    bool popBestTaskLocked(Task& out) {
        if (taskQ_.empty()) return false;
        int bestIdx = -1;
        int bestP = 999;
        for (int i=0; i<(int)taskQ_.size(); i++) {
            int p = pri(taskQ_[i].type);
            if (p < bestP) { bestP = p; bestIdx = i; }
            if (bestP == 0) break;
        }
        out = taskQ_[bestIdx];
        taskQ_.erase(taskQ_.begin() + bestIdx);
        return true;
    }

    // ============================================================
    // 新的 skip 規則：
    // - head 不能坐：不 rotate，不丟到後面
    //   只 head.skip_count++，然後看下一個誰能坐就坐誰
    // - head.skip_count >= maxSkips_ => forced：只能坐 head（head 不能坐就卡住）
    // ============================================================

    bool canSeatSomeoneNowLocked() const {
        if (waitingQ_.empty()) return false;

        // forced-head mode: only head allowed
        if (waitingQ_.front().skip_count >= maxSkips_) {
            auto c = waitingQ_.front().c;
            if (!c || c->seated) return false;
            return (bool)makePlanLocked(*c);
        }

        // normal mode: if ANY seatable exists, some waiter can seat
        for (auto& qc : waitingQ_) {
            if (!qc.c || qc.c->seated) continue;
            if (makePlanLocked(*qc.c)) return true;
        }
        return false;
    }

    // Return index to seat, and whether we just incremented head skip
    struct PickResult {
        int idx = -1;
        bool headSkipInc = false;
        int newHeadSkip = 0;
        bool forcedNow = false;
    };

    optional<PickResult> pickSeatableIndexHeadSkipNoRotateLocked() {
        if (waitingQ_.empty()) return nullopt;

        // forced-head mode
        if (waitingQ_.front().skip_count >= maxSkips_) {
            auto c0 = waitingQ_.front().c;
            if (!c0 || c0->seated) return nullopt;
            if (!makePlanLocked(*c0)) return nullopt;
            PickResult r;
            r.idx = 0;
            r.newHeadSkip = waitingQ_.front().skip_count;
            r.forcedNow = true;
            return r;
        }

        // normal mode
        auto c0 = waitingQ_.front().c;
        if (c0 && !c0->seated && makePlanLocked(*c0)) {
            PickResult r;
            r.idx = 0;
            r.newHeadSkip = waitingQ_.front().skip_count;
            return r;
        }

        // head cannot seat now -> increment skip_count (NO rotate)
        waitingQ_.front().skip_count++;
        PickResult r;
        r.headSkipInc = true;
        r.newHeadSkip = waitingQ_.front().skip_count;
        r.forcedNow = (waitingQ_.front().skip_count >= maxSkips_);

        // if increment makes it forced AND head still not seatable -> block now
        if (r.forcedNow) {
            auto c0b = waitingQ_.front().c;
            if (!c0b || c0b->seated) return nullopt;
            if (!makePlanLocked(*c0b)) return nullopt; // forced and still can't seat => BLOCK
            r.idx = 0; // actually can seat head now (rare but possible)
            return r;
        }

        // otherwise, try next customers (idx 1..n-1)
        for (int i = 1; i < (int)waitingQ_.size(); i++) {
            auto ci = waitingQ_[i].c;
            if (!ci || ci->seated) continue;
            if (makePlanLocked(*ci)) {
                r.idx = i;
                return r;
            }
        }

        // nobody seatable
        return nullopt;
    }

    // -----------------------------
    // Worker loop
    // -----------------------------
    void waiterLoop() {
        long long tid = thread_id_num();

        while (true) {
            unique_lock<mutex> lk(mu_);
            cvWork_.wait(lk, [&]{
                return stopAll_ || !taskQ_.empty() || canSeatSomeoneNowLocked();
            });
            if (stopAll_) return;

            activeWorkers_++;

            // 1) tasks first (RELEASE > PRELOAD_SEAT > ARRIVAL)
            Task task;
            if (popBestTaskLocked(task)) {
                auto c = task.c;

                if (task.type == TaskType::RELEASE) {
                    if (c && c->seated && T_ >= c->leaveTime) {
                        releaseLocked(*c);
                        logLineLocked(tid, *c, "release");
                    }
                } else if (task.type == TaskType::PRELOAD_SEAT) {
                    if (c) {
                        if (!everSatisfiableLocked(*c)) {
                            logLineLocked(tid, *c, "rejected");
                        } else {
                            c->arrived = true;
                            arrivedThisTime_.push_back(c);

                            auto plan = makePlanLocked(*c);
                            if (plan) {
                                applyPlanLocked(*c, *plan);
                                logLineLocked(tid, *c, "seated");
                                scheduleReleaseLocked(c);
                            } else {
                                waitingQ_.push_back(QueuedCustomer{c, 0});
                                logDebugLocked(tid, "PRELOAD queued (cannot seat now), ID=" + to_string(c->ID));
                            }
                        }
                    }
                } else { // ARRIVAL
                    if (c) {
                        if (!everSatisfiableLocked(*c)) {
                            logLineLocked(tid, *c, "rejected");
                        } else {
                            c->arrived = true;
                            arrivedThisTime_.push_back(c);
                            waitingQ_.push_back(QueuedCustomer{c, 0});
                            logDebugLocked(tid, "ARRIVAL queued, ID=" + to_string(c->ID));
                        }
                    }
                }

                activeWorkers_--;
                cvClock_.notify_one();
                cvWork_.notify_all();
                continue;
            }

            // 2) no tasks: try seat ONE customer with new skip policy (no rotate)
            {
                auto pick = pickSeatableIndexHeadSkipNoRotateLocked();
                if (pick) {
                    auto r = *pick;

                    // extra debug about head skip
                    if (!waitingQ_.empty() && waitingQ_.front().c) {
                        int hid = waitingQ_.front().c->ID;
                        if (r.headSkipInc) {
                            logDebugLocked(tid,
                                "HEAD cannot seat => skip_count++ (no rotate). headID=" + to_string(hid) +
                                " newSkip=" + to_string(r.newHeadSkip) +
                                (r.forcedNow ? " (FORCED NOW)" : ""));
                        } else {
                            logDebugLocked(tid,
                                "HEAD seatable or forced-seat. headID=" + to_string(hid) +
                                " skip=" + to_string(r.newHeadSkip));
                        }
                    }

                    if (r.idx >= 0 && r.idx < (int)waitingQ_.size()) {
                        auto c = waitingQ_[r.idx].c;
                        if (c && !c->seated) {
                            auto plan = makePlanLocked(*c);
                            if (plan) {
                                applyPlanLocked(*c, *plan);
                                // remove the seated one
                                waitingQ_.erase(waitingQ_.begin() + r.idx);

                                logLineLocked(tid, *c, "seated");
                                scheduleReleaseLocked(c);

                                if (r.idx != 0) {
                                    logDebugLocked(tid, "Seated from idx=" + to_string(r.idx) + " (head stayed).");
                                }
                            }
                        }
                    } else {
                        // pick returned but idx invalid (shouldn't happen)
                        logDebugLocked(tid, "pick returned invalid idx (BUG?)");
                        logWaitedOncePerTimeLocked(tid);
                    }
                } else {
                    // no seatable due to forced head or none seatable
                    if (!waitingQ_.empty() && waitingQ_.front().c) {
                        auto hid = waitingQ_.front().c->ID;
                        auto sk  = waitingQ_.front().skip_count;
                        logDebugLocked(tid, "No seatable now. headID=" + to_string(hid) + " skip=" + to_string(sk));
                    }
                    logWaitedOncePerTimeLocked(tid);
                }
            }

            activeWorkers_--;
            cvClock_.notify_one();
            cvWork_.notify_all();
        }
    }

    // -----------------------------
    // Clock loop
    // -----------------------------
    void clockLoop() {
        unique_lock<mutex> lk(mu_);

        while (true) {
            bool noFuture   = timeHeap_.empty();
            bool noTasks    = taskQ_.empty();
            bool noWaiting  = waitingQ_.empty();
            bool emptyBar   = !anyOccupiedLocked();
            bool noSeatable = !canSeatSomeoneNowLocked();

            if (!stopAll_ && noFuture && noTasks && noWaiting && emptyBar && activeWorkers_ == 0) {
                stopAll_ = true;
                cvWork_.notify_all();
                return;
            }

            // dead-end: have waiting but none seatable ever (bar empty, no future)
            if (!stopAll_ && noFuture && noTasks && !noWaiting && emptyBar && activeWorkers_ == 0 && noSeatable) {
                stopAll_ = true;
                cvWork_.notify_all();
                return;
            }

            cvClock_.wait(lk, [&]{
                return stopAll_ ||
                       (activeWorkers_ == 0 &&
                        taskQ_.empty() &&
                        !canSeatSomeoneNowLocked());
            });
            if (stopAll_) return;

            while (!timeHeap_.empty() && timeHeap_.top() < T_) timeHeap_.pop();
            if (timeHeap_.empty()) continue;

            int nextT = timeHeap_.top();
            timeHeap_.pop();
            while (!timeHeap_.empty() && timeHeap_.top() == nextT) timeHeap_.pop();

            T_ = nextT;

            arrivedThisTime_.clear();
            waitedPrintedAtTime_ = -1;

            // enqueue RELEASE first
            if (auto itR = releasesByTime_.find(nextT); itR != releasesByTime_.end()) {
                for (auto& c : itR->second) taskQ_.push_back(Task{TaskType::RELEASE, c});
                releasesByTime_.erase(itR);
            }
            // enqueue ARRIVAL
            if (auto itA = arrivalsByTime_.find(nextT); itA != arrivalsByTime_.end()) {
                for (auto& c : itA->second) taskQ_.push_back(Task{TaskType::ARRIVAL, c});
                arrivalsByTime_.erase(itA);
            }

            cvWork_.notify_all();
        }
    }

    // -----------------------------
    // Lifecycle
    // -----------------------------
    void startWaiters() {
        waiterThreads_.clear();
        for (int i=0; i<numWaiters_; i++) {
            waiterThreads_.emplace_back([this]{ waiterLoop(); });
        }
        cvWork_.notify_all();
    }

    void startClock() {
        clockThread_ = thread([this]{ clockLoop(); });
    }
};

// ============================================================
// main
// ============================================================
int main(int argc, char** argv) {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string csvPath = "base.csv";
    if (argc >= 2) csvPath = argv[1];

    // 只開 waiter 數量的 threads -> 預設 3
    SushiBarSimSafe sim(
        /*singles*/20, /*4P*/8, /*6P*/5, /*baby*/4, /*wheel*/2,
        /*waiters*/3,
        /*maxSkips*/3
    );

    vector<Customer> rows;
    try {
        rows = sim.readCSV(csvPath);
    } catch (const exception& e) {
        cerr << "read csv failed: " << e.what() << "\n";
        return 1;
    }

    sim.loadCustomers(rows);
    sim.runAll();
    return 0;
}
