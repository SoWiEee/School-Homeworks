# Rest: Sushi Bar Seating Simulator

這個資料夾是餐廳 / 壽司店座位資源配置模擬作業。程式讀取 CSV 中的客人到達事件，根據客人類型、同行人數、嬰兒椅需求、輪椅需求與用餐時間，模擬入座、等待與離席釋放資源的流程。

重點不是單純排序，而是處理有限資源下的同步問題：

- 多組客人可能同時到達。
- 座位、嬰兒椅、輪椅位都是共享資源。
- 有些客人需要特殊座位，例如嬰兒椅或無障礙座位。
- 已入座客人會在 `seat_time + est_dining_time` 後離席並釋放資源。
- 若隊首暫時無法入座，程式需要避免整個系統卡住。

## 檔案結構

```text
Rest/
├── main.cpp                 # 原始多執行緒 + TUI 版本
├── main_bypass.cpp          # 嘗試處理隊首阻塞 / bypass 的版本
├── sushi_safe.cpp           # 較穩定的 worker-thread 模擬版本，建議優先查看
├── output_rule.txt          # 指定輸出格式範例
├── dev_test/                # 開發測資
│   ├── base.csv
│   ├── deadlock.csv
│   ├── preoccupied.csv
│   └── race.csv
└── final_test/              # 正式測資
    ├── test_easy.csv
    ├── test_normal.csv
    ├── test_race_condition.csv
    ├── test_resource_exhaustion.csv
    └── test_complex.csv
```

## 問題設定

餐廳有三種座位與兩種輔助資源：

| 資源 | `main.cpp` 預設 | `sushi_safe.cpp` 預設 | 說明 |
|---|---:|---:|---|
| 單人座 `Sxx` | 20 | 20 | 可連續分配給多人的吧檯座位 |
| 四人沙發 `4Pxx` | 8 | 8 | 一組客人佔用一張 |
| 六人沙發 `6Pxx` | 5 | 5 | 一組客人佔用一張 |
| 嬰兒椅 `B` | 4 | 4 | `baby_chair` 欄位指定需求數 |
| 輪椅位 `W` | 2 | 2 | 輪椅客人或 `wheel_chair > 0` 會消耗 |

> 早期評分規格中也記錄過「單人座 14、四人沙發 5、六人沙發 3、嬰兒椅 3、輪椅 2」的初始值；目前程式碼實際使用的是上表的預設值。

## CSV 格式

每個測資檔包含表頭與 7 個欄位：

```csv
id,arrival_time,type,party_size,baby_chair,wheel_chair,est_dining_time
1,0,INDIVIDUAL,1,0,0,5
2,2,FAMILY,4,0,0,10
```

欄位說明：

| 欄位 | 說明 |
|---|---|
| `id` | 客人 ID。`-1` 表示開店前已在店內的預載客人，程式會轉成唯一負 ID |
| `arrival_time` | 到達時間。`-1` 表示預載客人 |
| `type` | 客人類型：`INDIVIDUAL`、`FAMILY`、`WITH_BABY`、`WHEELCHAIR` |
| `party_size` | 同行人數 |
| `baby_chair` | 需要的嬰兒椅數量 |
| `wheel_chair` | 需要的輪椅位數量 |
| `est_dining_time` | 預估用餐時間；離席時間為入座時間加上此欄位 |

程式的 parser 會忽略表頭，也會接受 `WHEELCHAALIR` 這個拼字錯誤並視為 `WHEELCHAIR`。

## 入座規則

`sushi_safe.cpp` 中的主要規則如下：

- `INDIVIDUAL`
  - 只處理 `party_size = 1` 的個人客。
  - 優先使用一個單人座。

- `WITH_BABY`
  - 需要連續的單人座，數量等於 `party_size`。
  - 同時消耗 `baby_chair` 指定數量的嬰兒椅。
  - 若沒有足夠連續單人座或嬰兒椅，進入等待。

- `WHEELCHAIR`
  - 必須使用無障礙沙發。
  - `party_size <= 4` 時優先使用 `4P01`，若不可用可 fallback 到 `6P01`。
  - `party_size >= 5` 時只能使用 `6P01`。
  - 至少消耗 1 個輪椅位，若 CSV 指定更多則依欄位消耗。

- `FAMILY`
  - 優先使用一般四人 / 六人沙發。
  - 一般沙發滿了才使用無障礙沙發。
  - 若沙發都不可用，嘗試降級為連續單人座。

`main.cpp` 的規則與 `sushi_safe.cpp` 很接近，但有 TUI 顯示與 one-thread-per-customer 的結構；`sushi_safe.cpp` 則改成固定 waiter threads，較容易避免 race condition 與輸出交錯。

## 等待與同步策略

`sushi_safe.cpp` 使用邏輯時鐘與 worker threads 模擬服務流程：

- 時間只跳到下一個 arrival 或 release event，不逐秒空轉。
- release task 優先於 arrival task，避免同一時間點資源釋放後卻沒被利用。
- 客人先進入等待佇列，再由 waiter thread 嘗試安排座位。
- 若隊首不能入座，不會直接把隊首旋轉到隊尾，而是增加 `skip_count`。
- 在 `skip_count < maxSkips` 時，後面的可入座客人可以先入座，避免 head-of-line blocking。
- 若隊首已被跳過 `maxSkips` 次，進入 forced-head 模式，只能先服務隊首；若仍無法入座，系統等待未來釋放事件。

目前 `sushi_safe.cpp` 預設：

```cpp
waiters = 3
maxSkips = 3
```

## 輸出格式

輸出格式參考 [output_rule.txt](output_rule.txt)：

```text
[Thread ID] [時間] [事件類型] ID: {id} | 需求: {資源需求} | 動作結果 | 剩餘資源: S={單人}, 4P={四人桌}, 6P={六人桌}, B={嬰兒椅}, W={輪椅}
```

常見事件：

- `seated`：成功入座，會附上座位 ID。
- `release`：用餐結束並釋放座位與輔助資源。
- `waited`：該時間點到達但暫時無法入座。
- `rejected`：需求在系統中永遠不可能被滿足，例如超過最大可容納人數。
- `[DEBUG]`：內部排程資訊，`sushi_safe.cpp` 可透過 `debug_` 控制。

範例：

```text
[704656] [5] [WITH_BABY] ID: 3 | 需求: 3 single_seats, 1 baby_chair | seated, id:[S01,S02,S03] | 剩餘資源: S=17, 4P=7, 6P=5, B=3, W=2
[998020] [23] [WHEELCHAIR] ID: 4 | 需求: 1 accessible_sofa (prefer 4P, fallback 6P), 1 wheelchair | release, id:[4P01] | 剩餘資源: S=20, 4P=8, 6P=4, B=4, W=2
```

## 編譯與執行

建議優先使用 `sushi_safe.cpp`：

```bash
cd Rest
g++ -std=c++17 -O2 -pthread sushi_safe.cpp -o sushi_safe
./sushi_safe dev_test/base.csv
```

Windows / PowerShell：

```powershell
cd Rest
g++ -std=c++17 -O2 -pthread sushi_safe.cpp -o sushi_safe.exe
.\sushi_safe.exe dev_test\base.csv
```

執行正式測資：

```powershell
.\sushi_safe.exe final_test\test_easy.csv
.\sushi_safe.exe final_test\test_normal.csv
.\sushi_safe.exe final_test\test_race_condition.csv
.\sushi_safe.exe final_test\test_resource_exhaustion.csv
.\sushi_safe.exe final_test\test_complex.csv
```

`main.cpp` 也可以編譯，但它會啟動終端機 TUI，輸出會持續刷新畫面：

```bash
g++ -std=c++17 -O2 -pthread main.cpp -o sushi_tui
./sushi_tui dev_test/base.csv
```

## 測資說明

### 開發測資

| 測資 | 用途 |
|---|---|
| `dev_test/base.csv` | 基本流程：到達、入座、離席釋放 |
| `dev_test/deadlock.csv` | 嬰兒椅不足造成等待，測試系統是否卡住 |
| `dev_test/race.csv` | 大量同時到達的個人客，測試同步與座位競爭 |
| `dev_test/preoccupied.csv` | 開店前已有客人佔位，測試預載客與後續到達 |

### 正式測資

| 測資 | 比重 | 重點 |
|---|---:|---|
| `final_test/test_easy.csv` | 15% | 基本入座與釋放 |
| `final_test/test_normal.csv` | 25% | 混合客型的一般案例 |
| `final_test/test_race_condition.csv` | 20% | 同時到達與多執行緒競爭 |
| `final_test/test_resource_exhaustion.csv` | 20% | 嬰兒椅 / 座位耗盡與等待 |
| `final_test/test_complex.csv` | 10% | 預載、特殊需求與複合排程 |
| 進階功能 | 10% | 家庭降級、輸出內容展示等 |

## Baseline FIFO 紀錄

README 早期紀錄的 FIFO baseline 如下，作為比較參考：

| Test Case | Last Seated | Last Departure |
|---|---:|---:|
| `test_easy.csv` | 47 | 75 |
| `test_normal.csv` | 34 | 63 |
| `test_race_condition.csv` | 28 | 51 |
| `test_resource_exhaustion.csv` | 548 | 999 |
| `test_complex.csv` | 248 | 999 |

這些數字代表單純 FIFO 策略下最後一組入座與最後離席時間；實際版本若允許隊首 bypass、家庭降級或不同資源策略，結果可能不同。

## 實作版本差異

- `main.cpp`
  - 一組到達客人一個 thread。
  - 內建 TUI，顯示目前時間、座位佔用、等待佇列與 recent logs。
  - 適合展示資源狀態，但輸出較不適合自動比對。

- `main_bypass.cpp`
  - 在 `main.cpp` 基礎上嘗試加入隊首 bypass 策略。
  - 保留 TUI 顯示。

- `sushi_safe.cpp`
  - 固定 3 個 waiter threads 處理 task。
  - release / preload / arrival 有明確優先順序。
  - 使用 head skip count 避免隊首阻塞。
  - 較適合作為最後提交或測試版本。
