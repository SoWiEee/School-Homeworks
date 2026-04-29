#include <algorithm>
#include <atomic>
#include <condition_variable>
#include <cctype>
#include <deque>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <optional>
#include <queue>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

using namespace std;

// Models / Parsing

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

struct Customer {
    int ID{};
    int ArrivalTime{};      // -1 = preloaded
    CustomerType Type{};
    int PartySize{};
    int BabyChair{};
    int WheelChair{};
    int EstDiningTime{};

    int ArrivalSeq{};       // deterministic FIFO insertion order
    int skipCount = 0;       // times this customer (as queue head) has been bypassed
    bool seated = false;

    int seatTime = -1;
    int leaveTime = -1;
    vector<string> seatIDs;
};

static vector<string> splitCSVLine(const string& line) {
    vector<string> out;
    string cur;
    bool inQuote = false;
    for (char ch : line) {
        if (ch == '"') inQuote = !inQuote;
        else if (ch == ',' && !inQuote) {
            out.push_back(trim(cur));
            cur.clear();
        } else cur.push_back(ch);
    }
    out.push_back(trim(cur));
    return out;
}

static bool isHeaderRow(const vector<string>& cols) {
    if (cols.empty()) return true;
    auto s0 = trim(cols[0]);
    if (s0.empty()) return true;
    bool allDigits = true;
    for (char c : s0) allDigits = allDigits && (isdigit((unsigned char)c) || c == '-' || c == '+');
    return !allDigits;
}

static vector<Customer> readCSV(const string& path) {
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
        c.ID = stoi(cols[0]);
        c.ArrivalTime = stoi(cols[1]);
        c.Type = parseType(cols[2]);
        c.PartySize = stoi(cols[3]);
        c.BabyChair = stoi(cols[4]);
        c.WheelChair = stoi(cols[5]);
        c.EstDiningTime = stoi(cols[6]);
        out.push_back(c);
    }
    return out;
}


// 要坐單人座連號、或 4 人沙發、或 6 人沙發
enum class PlanKind { Singles, Sofa4, Sofa6 };

// 計算出的分配方案
struct AllocationPlan {
    PlanKind kind{};
    vector<int> singleIdx;
    int sofaIdx = -1;
    int babyUse = 0;
    int wheelUse = 0;
    vector<string> seatIDs; // seat string
};

// 格式化座位 ID：prefix + 補零
static string fmtID(const string& prefix, int idx1based, int width) {
    ostringstream oss;
    oss << prefix << setw(width) << setfill('0') << idx1based;
    return oss.str();
}

// 把座位 ID list 串起來
static string joinIDs(const vector<string>& ids) {
    string out;
    for (size_t i = 0; i < ids.size(); i++) {
        if (i) out += " ";
        out += ids[i];
    }
    return out;
}

// 給 UI 顯示的狀態
struct Snapshot {
    int logicalTime = 0;
    int freeS = 0, free4 = 0, free6 = 0;
    int B = 0, W = 0;
    vector<int> singlesOcc; // size 20, 0 free else custID
    vector<int> sofa4Occ;   // size 8
    vector<int> sofa6Occ;   // size 5
    vector<int> waitingIDs;
    vector<string> recentLogs;
};

class SushiBar {
public:
    SushiBar(int singles = 20, int four = 8, int six = 5, int baby = 4, int wheel = 2)
        : totalBabyChairs_(baby),
          totalWheelSpots_(wheel),
          availBabyChairs_(baby),
          availWheelSpots_(wheel),
          seatsSingle_(singles, 0),
          sofas4P_(four, 0),
          sofas6P_(six, 0) {
        logicalTime_.store(0);  // atomic，避免 UI 讀取時不一致
        accessible4PIndex_ = (int)sofas4P_.size() - 1; // last 4P is accessible
        accessible6PIndex_ = (int)sofas6P_.size() - 1; // last 6P is accessible
    }

    // UI thread control
    void startUI() {
        uiStop_.store(false);
        uiThread_ = thread([this]{ this->uiLoop(); });
    }
    void stopUI() {
        uiStop_.store(true);
        // 通知 UI、客人、時鐘 thread 盡快醒來結束
        cv_.notify_all();
        cvClock_.notify_one();
        if (uiThread_.joinable()) uiThread_.join();
    }

    // 先把已在店內的人安排座位
    void preload(const vector<shared_ptr<Customer>>& initialCustomers) {
        unique_lock<mutex> lk(mu_);
        for (auto& c : initialCustomers) {
            int now = logicalTime_.load();
            auto plan = makePlanLocked(*c); // 嘗試算出可行分配方案
            if (!plan) {
                pushLogLocked(*c, now, "PRELOAD_FAILED", {});
                continue;
            }
            // 扣資源 + 佔位
            applyPlanLocked(*c, *plan, now);
            pushLogLocked(*c, now, "PRE-SEATED", c->seatIDs);

            // 把 leaveTime 加入 timeHeap
            int leave = now + c->EstDiningTime;
            c->leaveTime = leave;
            timeHeap_.push(leave);
        }
        cvClock_.notify_one();  // 通知 clock thread
        cv_.notify_all();
    }

    // 預載客人的 thread：等到 leaveTime 時 release
    void handlePreloaded(shared_ptr<Customer> c) {
        unique_lock<mutex> lk(mu_);

        // 若預載入座失敗（或未配置 leaveTime），視為已完成，避免卡住結束條件
        if (!c->seated || c->leaveTime < 0) {
            finishedCount_++;
            cv_.notify_all();
            cvClock_.notify_one();
            return;
        }

        // 等到 logicalTime >= leaveTime
        cv_.wait(lk, [&]{ return stopClock_ || (logicalTime_.load() >= c->leaveTime); });
        if (stopClock_) return;

        // release rsrc
        releaseLocked(*c);
        pushLogLocked(*c, logicalTime_.load(), "RELEASE", c->seatIDs);

        // 此組完成（預載客人也需要納入結束條件）
        finishedCount_++;

        // 通知大家可能有人可以入座了
        cv_.notify_all();
        cvClock_.notify_one();
    }

    //  把所有到達客人的 ArrivalTime 登記到 timeHeap
    void registerArrivalTimes(const vector<shared_ptr<Customer>>& incomingCustomers) {
        unique_lock<mutex> lk(mu_);
        for (auto& c : incomingCustomers) {
            if (c->ArrivalTime >= 0) timeHeap_.push(c->ArrivalTime);
        }
        cvClock_.notify_one();
    }

    // logical clock thread
    void startClock() {
        stopClock_ = false;
        clockThread_ = thread([this]{ this->clockLoop(); });
    }
    void stopClock() {
        {
            lock_guard<mutex> lk(mu_);
            stopClock_ = true;
            cv_.notify_all();
            cvClock_.notify_one();
        }
        if (clockThread_.joinable()) clockThread_.join();
    }

    // handleCustomer：每組 arriving 客人一個 thread 跑這裡
    void handleCustomer(shared_ptr<Customer> c) {
        unique_lock<mutex> lk(mu_);
        // 等到 logicalTime >= ArrivalTime 且 nextArrivalSeq == ArrivalSeq
        cv_.wait(lk, [&]{
            return stopClock_ || (logicalTime_.load() >= c->ArrivalTime && nextArrivalSeq_.load() == c->ArrivalSeq);
        });
        if (stopClock_) return;

        // 到達處理名額往後移
        nextArrivalSeq_++;

        // 檢查永遠不可滿足的需求
        if (!isEverSatisfiableLocked(*c)) {
            pushLogLocked(*c, logicalTime_.load(), "rejected", {});
            finishedCount_++;
            cv_.notify_all();
            cvClock_.notify_one();
            return;
        }

        // enqueue customer
        queue_.push_back(c);
        // notify: queue changed (may enable bypass seating)
        cv_.notify_all();


        // Initial action after enqueue:
        // - FIFO if head is feasible now.
        // - If head is blocking, we may seat a non-head (limited bypass) until bypass limit is reached.
        if (!queue_.empty() && queue_.front().get() == c.get()) {
            if (!trySeatOneLocked(logicalTime_.load())) {
                pushLogLocked(*c, logicalTime_.load(), "waited", {});
            } else if (!c->seated) {
                // Someone else might have been seated (possible if multiple arrivals were enqueued at the same time).
                pushLogLocked(*c, logicalTime_.load(), "waited", {});
            }
        } else {
            // Not head => wait.
            pushLogLocked(*c, logicalTime_.load(), "waited", {});
        }
        
        
        // 醒來檢查自己是否已變 head，且現在是否有資源可用
        while (!c->seated) {
            cv_.wait(lk, [&]{
                if (stopClock_) return true;
                if (c->seated) return true;

                // Only the queue head acts as the scheduler:
                // attempt to seat exactly one group under the limited-bypass policy.
                if (!queue_.empty() && queue_.front().get() == c.get()) {
                    if (trySeatOneLocked(logicalTime_.load())) {
                    return true;    // someone seated; wake and re-check
                    }
                }
                return false;   // sleep
            });
            if (stopClock_) return;
        }

        // 等到離席時間
        cv_.wait(lk, [&]{ return stopClock_ || (logicalTime_.load() >= c->leaveTime); });
        if (stopClock_) return;

        // 釋放資源 + 寫 log
        releaseLocked(*c);
        pushLogLocked(*c, logicalTime_.load(), "RELEASE", c->seatIDs);

        finishedCount_++;
        // 釋放後通知其他等待者
        cv_.notify_all();
        cvClock_.notify_one();
    }


    // Limited-bypass FIFO scheduler:
    // - If head can be seated now => seat head (strict FIFO).
    // - If head cannot be seated now:
    //     * If head.skipCount >= kMaxBypass => strict FIFO: seat nobody until head becomes feasible.
    //     * Else => seat the first non-head in queue that is feasible now (one per call), and increment head.skipCount.
    // Returns true if someone was seated.
    bool trySeatOneLocked(int now) {
        if (queue_.empty()) return false;

        auto head = queue_.front();
        if (!head || head->seated) return false;

        // Strict FIFO mode after too many bypasses.
        if (head->skipCount >= kMaxBypass) {
            auto planHead = makePlanLocked(*head);
            if (!planHead) return false;

            applyPlanLocked(*head, *planHead, now);
            queue_.pop_front();
            pushLogLocked(*head, now, "seated", head->seatIDs);

            head->leaveTime = head->seatTime + head->EstDiningTime;
            timeHeap_.push(head->leaveTime);

            cvClock_.notify_one();
            cv_.notify_all();
            return true;
        }

        // Normal FIFO if head is feasible now.
        if (auto planHead = makePlanLocked(*head)) {
            applyPlanLocked(*head, *planHead, now);
            queue_.pop_front();
            pushLogLocked(*head, now, "seated", head->seatIDs);

            head->leaveTime = head->seatTime + head->EstDiningTime;
            timeHeap_.push(head->leaveTime);

            cvClock_.notify_one();
            cv_.notify_all();
            return true;
        }

        // Head is blocking; allow bypass (up to kMaxBypass times).
        for (auto it = next(queue_.begin()); it != queue_.end(); ++it) {
            auto cand = *it;
            if (!cand || cand->seated) continue;

            auto plan = makePlanLocked(*cand);
            if (!plan) continue;

            applyPlanLocked(*cand, *plan, now);
            queue_.erase(it);
            pushLogLocked(*cand, now, "seated", cand->seatIDs);

            cand->leaveTime = cand->seatTime + cand->EstDiningTime;
            timeHeap_.push(cand->leaveTime);

            head->skipCount++;
            pushLogLocked(*head, now, "waited", {});

            cvClock_.notify_one();
            cv_.notify_all();
            return true;
        }

        return false;
    }

    // 等所有 arriving customers 做完 (finishedCount >= totalCustomers)
    void waitAll(int totalCustomers) {
        unique_lock<mutex> lk(mu_);
        cv_.wait(lk, [&]{ return finishedCount_.load() >= totalCustomers; });
    }

    // 平均等待時間（ArrivalTime >= 0 的客人）統計：回傳 (sum_wait_time, seated_count)
    pair<long long, int> getWaitingStats() const {
        return { waitSum_.load(), waitCount_.load() };
    }

    double getAverageWaitingTime() const {
        const long long sum = waitSum_.load();
        const int cnt = waitCount_.load();
        return (cnt > 0) ? (double)sum / (double)cnt : 0.0;
    }

private:
    // sync
    mutex mu_;
    condition_variable cv_;
    condition_variable cvClock_;
    thread clockThread_;

    atomic<int> logicalTime_{0};
    atomic<int> nextArrivalSeq_{0};
    atomic<int> finishedCount_{0};
    // waiting time stats (ArrivalTime >= 0, seated only)
    atomic<long long> waitSum_{0};
    atomic<int> waitCount_{0};
    bool stopClock_ = false;

    // 未來時間點：最小的時間會先出 (min-heap)
    priority_queue<int, vector<int>, greater<int>> timeHeap_;

    // resources
    const int totalBabyChairs_;
    const int totalWheelSpots_;
    int availBabyChairs_;
    int availWheelSpots_;

    // 座位佔用表：0 空位、非 0 表示該客人 ID 佔用
    vector<int> seatsSingle_;
    vector<int> sofas4P_;
    vector<int> sofas6P_;

    // 無障礙沙發
    int accessible4PIndex_;
    int accessible6PIndex_;

    deque<shared_ptr<Customer>> queue_;

    // logs for TUI
    deque<string> recentLogs_;
    vector<string> allLogs_;

    static constexpr int kRecentLogMax = 18;
    static constexpr int kMaxBypass = 3; // head can be bypassed at most this many times

    // UI thread
    atomic<bool> uiStop_{false};
    thread uiThread_;

private:
    bool isEverSatisfiableLocked(const Customer& c) const {
        if (c.PartySize < 1 || c.PartySize > 6) return false;
        if (c.BabyChair < 0 || c.WheelChair < 0) return false;
        if (c.BabyChair > totalBabyChairs_) return false;
        if (c.WheelChair > totalWheelSpots_) return false;
        return true;
    }

    // 尋找 k 個連續空的單人座
    optional<vector<int>> findContinuousSinglesLocked(int k) const {
        int n = (int)seatsSingle_.size();
        if (k <= 0 || k > n) return nullopt;
        int cnt = 0, start = 0;
        for (int i = 0; i < n; i++) {
            if (seatsSingle_[i] == 0) {
                if (cnt == 0) start = i;
                cnt++;
                if (cnt == k) {
                    vector<int> idxs;
                    for (int j = 0; j < k; j++) idxs.push_back(start + j);
                    return idxs;
                }
            } else cnt = 0;
        }
        return nullopt;
    }

    // 找一張空的沙發
    optional<int> findFreeSofaLocked(const vector<int>& sofas, int begin, int endExclusive) const {
        for (int i = begin; i < endExclusive; i++) {
            if (sofas[i] == 0) return i;
        }
        return nullopt;
    }

    // 計算分配計畫 (locked)
    // - 資源不足 => 回傳 nullopt
    optional<AllocationPlan> makePlanLocked(const Customer& c) const {
        AllocationPlan plan;
        if (c.BabyChair > availBabyChairs_) return nullopt;
        if (c.WheelChair > availWheelSpots_) return nullopt;

        plan.babyUse = c.BabyChair;
        plan.wheelUse = c.WheelChair;

        switch (c.Type) {
            case CustomerType::INDIVIDUAL: {
                // 1 single else sofa
                for (int i = 0; i < (int)seatsSingle_.size(); i++) {
                    if (seatsSingle_[i] == 0) {
                        plan.kind = PlanKind::Singles;
                        plan.singleIdx = {i};
                        plan.seatIDs = { fmtID("S", i + 1, 2) };
                        return plan;
                    }
                }
                if (auto idx = findFreeSofaLocked(sofas4P_, 0, (int)sofas4P_.size())) {
                    plan.kind = PlanKind::Sofa4;
                    plan.sofaIdx = *idx;
                    plan.seatIDs = { fmtID("4P", *idx + 1, 2) };
                    return plan;
                }
                if (auto idx = findFreeSofaLocked(sofas6P_, 0, (int)sofas6P_.size())) {
                    plan.kind = PlanKind::Sofa6;
                    plan.sofaIdx = *idx;
                    plan.seatIDs = { fmtID("6P", *idx + 1, 2) };
                    return plan;
                }
                return nullopt;
            }

            case CustomerType::WHEELCHAIR: {
                // must use accessible sofa; consume wheel spots
                if (c.PartySize <= 4) {
                    if (sofas4P_[accessible4PIndex_] == 0) {
                        plan.kind = PlanKind::Sofa4;
                        plan.sofaIdx = accessible4PIndex_;
                        plan.seatIDs = { fmtID("4P", accessible4PIndex_ + 1, 2) };
                        return plan;
                    }
                }
                if (c.PartySize <= 6) {
                    if (sofas6P_[accessible6PIndex_] == 0) {
                        plan.kind = PlanKind::Sofa6;
                        plan.sofaIdx = accessible6PIndex_;
                        plan.seatIDs = { fmtID("6P", accessible6PIndex_ + 1, 2) };
                        return plan;
                    }
                }
                return nullopt;
            }

            case CustomerType::WITH_BABY: {
                // (A) consecutive singles
                if (auto idxs = findContinuousSinglesLocked(c.PartySize)) {
                    plan.kind = PlanKind::Singles;
                    plan.singleIdx = *idxs;
                    plan.seatIDs.clear();
                    for (int i : *idxs) plan.seatIDs.push_back(fmtID("S", i + 1, 2));
                    return plan;
                }

                // (B) sofa fallback
                if (c.PartySize <= 4) {
                    if (auto idx = findFreeSofaLocked(sofas4P_, 0, (int)sofas4P_.size())) {
                        plan.kind = PlanKind::Sofa4;
                        plan.sofaIdx = *idx;
                        plan.seatIDs = { fmtID("4P", *idx + 1, 2) };
                        return plan;
                    }
                }
                if (c.PartySize <= 6) {
                    if (auto idx = findFreeSofaLocked(sofas6P_, 0, (int)sofas6P_.size())) {
                        plan.kind = PlanKind::Sofa6;
                        plan.sofaIdx = *idx;
                        plan.seatIDs = { fmtID("6P", *idx + 1, 2) };
                        return plan;
                    }
                }
                return nullopt;
            }

            case CustomerType::FAMILY: {
                // wheelchair family => accessible only
                if (c.WheelChair > 0) {
                    if (c.PartySize <= 4 && sofas4P_[accessible4PIndex_] == 0) {
                        plan.kind = PlanKind::Sofa4;
                        plan.sofaIdx = accessible4PIndex_;
                        plan.seatIDs = { fmtID("4P", accessible4PIndex_ + 1, 2) };
                        return plan;
                    }
                    if (c.PartySize <= 6 && sofas6P_[accessible6PIndex_] == 0) {
                        plan.kind = PlanKind::Sofa6;
                        plan.sofaIdx = accessible6PIndex_;
                        plan.seatIDs = { fmtID("6P", accessible6PIndex_ + 1, 2) };
                        return plan;
                    }
                    return nullopt;
                }

                // prefer normal sofas (exclude accessible)
                if (c.PartySize <= 4) {
                    if (auto idx = findFreeSofaLocked(sofas4P_, 0, accessible4PIndex_)) {
                        plan.kind = PlanKind::Sofa4;
                        plan.sofaIdx = *idx;
                        plan.seatIDs = { fmtID("4P", *idx + 1, 2) };
                        return plan;
                    }
                }
                if (c.PartySize <= 6) {
                    if (auto idx = findFreeSofaLocked(sofas6P_, 0, accessible6PIndex_)) {
                        plan.kind = PlanKind::Sofa6;
                        plan.sofaIdx = *idx;
                        plan.seatIDs = { fmtID("6P", *idx + 1, 2) };
                        return plan;
                    }
                }

                // allow accessible if normal full
                if (c.PartySize <= 4 && sofas4P_[accessible4PIndex_] == 0) {
                    plan.kind = PlanKind::Sofa4;
                    plan.sofaIdx = accessible4PIndex_;
                    plan.seatIDs = { fmtID("4P", accessible4PIndex_ + 1, 2) };
                    return plan;
                }
                if (c.PartySize <= 6 && sofas6P_[accessible6PIndex_] == 0) {
                    plan.kind = PlanKind::Sofa6;
                    plan.sofaIdx = accessible6PIndex_;
                    plan.seatIDs = { fmtID("6P", accessible6PIndex_ + 1, 2) };
                    return plan;
                }

                // downgrade
                if (c.PartySize == 4) {
                    if (auto idxs = findContinuousSinglesLocked(4)) {
                        plan.kind = PlanKind::Singles;
                        plan.singleIdx = *idxs;
                        plan.seatIDs.clear();
                        for (int i : *idxs) plan.seatIDs.push_back(fmtID("S", i + 1, 2));
                        return plan;
                    }
                }

                return nullopt;
            }

            default:
                return nullopt;
        }
    }

    // 真正扣資源 + 佔位的地方
    void applyPlanLocked(Customer& c, const AllocationPlan& plan, int now) {
        availBabyChairs_ -= plan.babyUse;
        availWheelSpots_ -= plan.wheelUse;

        // 佔位（把座位/沙發陣列填入客人 ID）
        if (plan.kind == PlanKind::Singles) {
            for (int idx : plan.singleIdx) seatsSingle_[idx] = c.ID;
        } else if (plan.kind == PlanKind::Sofa4) {
            sofas4P_[plan.sofaIdx] = c.ID;
        } else {
            sofas6P_[plan.sofaIdx] = c.ID;
        }

        // update state
        c.seated = true;
        c.seatTime = now;
        c.seatIDs = plan.seatIDs;

        // waiting time stats: only count customers that actually "arrive" (ArrivalTime >= 0)
        if (c.ArrivalTime >= 0) {
            long long wt = (long long)now - (long long)c.ArrivalTime;
            if (wt < 0) wt = 0;
            waitSum_.fetch_add(wt);
            waitCount_.fetch_add(1);
        }
    }

    // 釋放資源與座位
    void releaseLocked(Customer& c) {
        availBabyChairs_ += c.BabyChair;
        availWheelSpots_ += c.WheelChair;

        // 依 seatIDs 把陣列中的佔用清回 0
        for (const auto& id : c.seatIDs) {
            if (!id.empty() && id[0] == 'S') {
                int idx = stoi(id.substr(1));
                seatsSingle_[idx - 1] = 0;
            } else if (id.rfind("4P", 0) == 0) {
                int idx = stoi(id.substr(2));
                sofas4P_[idx - 1] = 0;
            } else if (id.rfind("6P", 0) == 0) {
                int idx = stoi(id.substr(2));
                sofas6P_[idx - 1] = 0;
            }
        }
    }

    // 計算剩餘資源（顯示用）
    int countFreeSinglesLocked() const {
        int cnt = 0; for (int v : seatsSingle_) if (v == 0) cnt++; return cnt;
    }
    int countFree4Locked() const {
        int cnt = 0; for (int v : sofas4P_) if (v == 0) cnt++; return cnt;
    }
    int countFree6Locked() const {
        int cnt = 0; for (int v : sofas6P_) if (v == 0) cnt++; return cnt;
    }

    // 把需求顯示成文字
    string demandStringLocked(const Customer& c, const vector<string>& seatIDs) const {
        vector<string> parts;

        int singlesUsed = 0;
        bool used4 = false, used6 = false;
        for (auto& id : seatIDs) {
            if (!id.empty() && id[0] == 'S') singlesUsed++;
            if (id.rfind("4P", 0) == 0) used4 = true;
            if (id.rfind("6P", 0) == 0) used6 = true;
        }

        switch (c.Type) {
            case CustomerType::INDIVIDUAL:
                if (used4) parts.push_back("1 four_seat_sofa");
                else if (used6) parts.push_back("1 six_seat_sofa");
                else parts.push_back("1 single_seat");
                break;
            case CustomerType::WHEELCHAIR:
                parts.push_back((c.PartySize <= 4) ? "1 four_seat_sofa" : "1 six_seat_sofa");
                parts.push_back(to_string(c.WheelChair) + " wheelchair");
                if (c.BabyChair > 0) parts.push_back(to_string(c.BabyChair) + " baby_chair");
                break;
            case CustomerType::WITH_BABY:
                if (used4) parts.push_back("1 four_seat_sofa");
                else if (used6) parts.push_back("1 six_seat_sofa");
                // else parts.push_back(to_string(max(0, singlesUsed)) + " single_seats");
                else parts.push_back(to_string(c.PartySize) + " single_seats");
                parts.push_back(to_string(c.BabyChair) + " baby_chair");
                if (c.WheelChair > 0) parts.push_back(to_string(c.WheelChair) + " wheelchair");
                break;
            case CustomerType::FAMILY:
                if (used4) parts.push_back("1 four_seat_sofa");
                else if (used6) parts.push_back("1 six_seat_sofa");
                else if (singlesUsed > 0) parts.push_back(to_string(singlesUsed) + " single_seats");
                else parts.push_back((c.PartySize <= 4) ? "1 four_seat_sofa" : "1 six_seat_sofa");
                if (c.WheelChair > 0) parts.push_back(to_string(c.WheelChair) + " wheelchair");
                if (c.BabyChair > 0) parts.push_back(to_string(c.BabyChair) + " baby_chair");
                break;
            default:
                break;
        }

        string out;
        for (size_t i = 0; i < parts.size(); i++) {
            if (i) out += ", ";
            out += parts[i];
        }
        return out;
    }

    // 產生一行 log
    // - 顯示時間、類型、需求、結果、剩餘資源
    string formatLogLocked(const Customer& c, int now, const string& action, const vector<string>& ids) const {
        std::thread::id threadID = std::this_thread::get_id();

        // preloaded => INIT
        string timeStr = (c.ArrivalTime == -1 && action == "PRE-SEATED") ? string("INIT") : to_string(now);
        string reqStr = demandStringLocked(c, ids.empty() ? c.seatIDs : ids);

        string resultStr = action;
        if (!ids.empty() && (action == "seated" || action == "RELEASE" || action == "PRE-SEATED")) {
            resultStr += ", id:[" + joinIDs(ids) + "]";
        } else if (!c.seatIDs.empty() && (action == "RELEASE")) {
            resultStr += ", id:[" + joinIDs(c.seatIDs) + "]";
        }

        ostringstream oss;
        oss << "[" << threadID << "] "
            << "[" << timeStr << "] "
            << "[" << typeLabel(c.Type) << "] "
            << "ID: " << c.ID
            << " | 需求: " << reqStr
            << " | " << resultStr
            << " | 剩餘資源: S=" << countFreeSinglesLocked()
            << ", 4P=" << countFree4Locked()
            << ", 6P=" << countFree6Locked()
            << ", B=" << availBabyChairs_
            << ", W=" << availWheelSpots_;
        return oss.str();
    }

    // Push a structured log entry, with a small UX improvement:
    // If we already logged "waited" for the same customer at the same time,
    // and later in the same time we log a terminal/decisive outcome (e.g., "seated"),
    // we replace the earlier "waited" entry instead of appending a second line.
    void pushLogLocked(const Customer& c, int now, const string& action, const vector<string>& ids) {
        string line = formatLogLocked(c, now, action, ids);

        const bool isDecisive = (action == "seated" || action == "rejected" || action == "PRE-SEATED" || action == "RELEASE");
        if (isDecisive) {
            string timeTok = "[" + to_string(now) + "]";
            string idTok = "ID: " + to_string(c.ID);

            auto isSameWaited = [&](const string& s) {
                return (s.find(timeTok) != string::npos) && (s.find(idTok) != string::npos) && (s.find("| waited |") != string::npos);
            };

            // Replace the latest matching waited log (if any) in allLogs_ and recentLogs_.
            for (int i = (int)allLogs_.size() - 1; i >= 0; --i) {
                if (!isSameWaited(allLogs_[i])) continue;
                allLogs_[i] = line;
                for (int j = (int)recentLogs_.size() - 1; j >= 0; --j) {
                    if (isSameWaited(recentLogs_[j])) { recentLogs_[j] = line; break; }
                }
                return;
            }
        }

        // Default: append.
        pushLogLocked(line);
    }

    void pushLogLocked(const string& line) {
        allLogs_.push_back(line);
        recentLogs_.push_back(line);
        while ((int)recentLogs_.size() > kRecentLogMax) recentLogs_.pop_front();
    }

    // - 從 timeHeap_ 拿下一個事件時間 nextT
    // - cv_.notify_all() 叫醒所有等待 arrival / seat / leave 的 thread
    void clockLoop() {
        while (true) {
            int nextT = -1;

            {
                unique_lock<mutex> lk(mu_);
                // 等到：
                // - stopClock_，或 timeHeap_ 有事件時間點
                cvClock_.wait(lk, [&]{ return stopClock_ || !timeHeap_.empty(); });
                if (stopClock_) return;

                // 把已經過期或等於目前時間的事件丟掉
                while (!timeHeap_.empty() && timeHeap_.top() <= logicalTime_.load()) timeHeap_.pop();
                if (timeHeap_.empty()) continue;

                // 下一個事件時間
                nextT = timeHeap_.top();
                timeHeap_.pop();
                logicalTime_.store(nextT);  // 時間跳到 nextT

                // notify all waiter threads & UI
                cv_.notify_all();
            }

            // UI refresh interval: 0.8s
            this_thread::sleep_for(chrono::milliseconds(800));
        }
    }

    // TUI snapshot
    Snapshot snapshotLocked() const {
        Snapshot s;
        s.logicalTime = logicalTime_.load();
        s.freeS = countFreeSinglesLocked();
        s.free4 = countFree4Locked();
        s.free6 = countFree6Locked();
        s.B = availBabyChairs_;
        s.W = availWheelSpots_;
        s.singlesOcc = seatsSingle_;
        s.sofa4Occ = sofas4P_;
        s.sofa6Occ = sofas6P_;
        for (auto& p : queue_) s.waitingIDs.push_back(p->ID);
        s.recentLogs.assign(recentLogs_.begin(), recentLogs_.end());
        return s;
    }

    // uiLoop：每 0.8 秒刷新一次
    // - 會 wait_for 0.8s 或等到 cv_ 通知
    // - 取 snapshot 後解鎖，再輸出
    void uiLoop() {
        while (!uiStop_.load()) {
            Snapshot snap;
            {
                unique_lock<mutex> lk(mu_);
                // wait either a notify, or timeout 0.8s
                cv_.wait_for(lk, chrono::milliseconds(800));
                snap = snapshotLocked();
            }

            cout << "\x1b[2J\x1b[H";
            cout << "=== SushiBar ===\n";
            cout << "LogicalTime T = " << snap.logicalTime << "\n";
            cout << "Resources: S=" << snap.freeS
                 << "  4P=" << snap.free4
                 << "  6P=" << snap.free6
                 << "  B=" << snap.B
                 << "  W=" << snap.W << "\n\n";

            // Singles
            cout << "Singles (S01..S20):\n";
            for (int i = 0; i < (int)snap.singlesOcc.size(); i++) {
                if (i % 10 == 0) cout << "  ";
                if (snap.singlesOcc[i] == 0) {
                    cout << "[  . ]";
                } else {
                    ostringstream cell;
                    cell << snap.singlesOcc[i];
                    string v = cell.str();
                    if (v.size() > 3) v = v.substr(v.size() - 3);
                    cout << "[" << setw(3) << v << " ]";
                }
                if (i % 10 == 9) cout << "\n";
            }
            cout << "\n";

            // 4P
            cout << "4P Sofas (4P01..4P08; 4P08 accessible):\n  ";
            for (int i = 0; i < (int)snap.sofa4Occ.size(); i++) {
                if (snap.sofa4Occ[i] == 0) cout << "[ . ]";
                else {
                    ostringstream cell; cell << snap.sofa4Occ[i];
                    string v = cell.str(); if (v.size() > 3) v = v.substr(v.size() - 3);
                    cout << "[" << setw(3) << v << "]";
                }
                if (i == (int)snap.sofa4Occ.size() - 1) cout << "  (accessible)\n";
            }
            cout << "\n";

            // 6P
            cout << "6P Sofas (6P01..6P05; 6P05 accessible):\n  ";
            for (int i = 0; i < (int)snap.sofa6Occ.size(); i++) {
                if (snap.sofa6Occ[i] == 0) cout << "[ . ]";
                else {
                    ostringstream cell; cell << snap.sofa6Occ[i];
                    string v = cell.str(); if (v.size() > 3) v = v.substr(v.size() - 3);
                    cout << "[" << setw(3) << v << "]";
                }
                if (i == (int)snap.sofa6Occ.size() - 1) cout << "  (accessible)\n";
            }
            cout << "\n";

            // Waiting queue
            cout << "Waiting Queue (FIFO head -> tail): ";
            if (snap.waitingIDs.empty()) cout << "(empty)\n";
            else {
                for (size_t i = 0; i < snap.waitingIDs.size(); i++) {
                    if (i) cout << " -> ";
                    cout << snap.waitingIDs[i];
                }
                cout << "\n";
            }

            cout << "\nRecent Events:\n";
            for (auto& line : snap.recentLogs) cout << "  " << line << "\n";

            cout << "\n(Press Ctrl+C to quit)\n";
            cout.flush();
        }
    }
};

// Main routine

int main(int argc, char** argv) {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string csvPath = "base.csv";
    if (argc >= 2) csvPath = argv[1];

    // read csv
    vector<Customer> rows;
    try {
        rows = readCSV(csvPath);
    } catch (const exception& e) {
        cerr << "read csv failed: " << e.what() << "\n";
        return 1;
    }

    vector<shared_ptr<Customer>> initialCustomers;
    vector<shared_ptr<Customer>> incomingCustomers;

    int tempIDCounter = -1;
    for (auto& r : rows) {
        auto c = make_shared<Customer>(r);
        if (c->ID == -1) c->ID = tempIDCounter--; // unique negative IDs for preloaded
        if (c->ArrivalTime == -1) initialCustomers.push_back(c);
        else incomingCustomers.push_back(c);
    }

    // 依 arrival time，再依 id 排序，並給 ArrivalSeq
    // 同一時間到達的客人也會有固定順序
    stable_sort(incomingCustomers.begin(), incomingCustomers.end(),
        [](const auto& a, const auto& b){
            if (a->ArrivalTime != b->ArrivalTime) return a->ArrivalTime < b->ArrivalTime;
            return a->ID < b->ID;
        }
    );
    for (int i = 0; i < (int)incomingCustomers.size(); i++) incomingCustomers[i]->ArrivalSeq = i;

    SushiBar bar;

    bar.startUI();

    cout << "=== Initializing (preload) ===\n";
    bar.preload(initialCustomers);
    cout << "=== Start service ===\n";

    // 登記所有 arrival time，然後啟動 logical clock
    bar.registerArrivalTimes(incomingCustomers);
    bar.startClock();

    // preloaded release threads
    vector<thread> preloadThreads;
    preloadThreads.reserve(initialCustomers.size());
    for (auto& c : initialCustomers) {
        preloadThreads.emplace_back([&bar, c]{ bar.handlePreloaded(c); });
    }

    // one thread per arriving customer group (required by assignment)
    vector<thread> threads;
    threads.reserve(incomingCustomers.size());
    for (auto& c : incomingCustomers) {
        threads.emplace_back([&bar, c]{ bar.handleCustomer(c); });
    }

    // wait all customers (arriving + preloaded)
    bar.waitAll((int)(incomingCustomers.size() + initialCustomers.size()));

    // end
    bar.stopClock();
    for (auto& th : threads) if (th.joinable()) th.join();
    for (auto& th : preloadThreads) if (th.joinable()) th.join();
    bar.stopUI();

    // Print average waiting time (ArrivalTime >= 0, seated only)
    auto [waitSum, waitCnt] = bar.getWaitingStats();
    cout << "\n=== Statistics ===\n";
    cout << "Seated groups counted for waiting time: " << waitCnt << "\n";
    if (waitCnt > 0) {
        cout << "Average waiting time (T_seated - T_arrival): "
             << fixed << setprecision(2) << bar.getAverageWaitingTime() << "\n";
    } else {
        cout << "Average waiting time (T_seated - T_arrival): N/A (no arriving groups seated)\n";
    }

    return 0;
}
