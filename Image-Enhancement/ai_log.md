# AI 協作紀錄

**工具**：Claude Sonnet 4.6（Anthropic Claude Code CLI）  
**協作期間**：2026-04-18  
**專案**：Image-Enhancement（影像強化的選擇與代價）

---

## 協作流程總覽

| # | 使用者 Prompt（摘要） | AI 行為 | 驗證方式 | 發現的 AI 缺失 |
|---|------|---------|---------|--------------|
| 1 | 閱讀 project.pdf，實作 task_a.m，更新 README Task A | 生成統計迴圈、直方圖輸出程式碼 | `matlab -batch` 執行確認數值 | 初版未處理 T01 灰階影像，導致 `rgb2gray` 報錯 |
| 2 | 實作 task_b.m，比較兩種方法 | 生成 P01/P02/P03 三段比較程式碼 | 執行確認 `histeq` 等函式可用 | 未預先偵測 IPT 是否安裝，直接使用 `histeq` 導致錯誤 |
| 3 | IPT 未安裝，嘗試安裝或手動實作 | 提供 `histeq_m`、`clahe_m`、`rgb2ycbcr_m` 手動實作 | 執行確認數值正確 | CLAHE 手動實作的雙線性插值索引有偏移錯誤，需修正 |
| 4 | 安裝好 IPT，改用官方函式 | 重寫 task_b.m 使用 `histeq`、`adapthisteq`、`rgb2ycbcr` | 執行確認數值一致 | `sprintf('Gamma \gamma=...')` 逸出字元警告，需改為 `\\gamma` |
| 5 | 補充 R/G/B/\|R-B\| 欄位及各方法優缺點 | 擴充 fprintf 輸出與 README 表格 | 核對各通道數值 | — |
| 6 | task_b 輸出個別增強圖片到 output/task_b/ | 加入 `imwrite` 呼叫與目錄建立 | `output/task_b/` 確認 6 張圖 | 原版 `saveas` 路徑仍指向 `output/`，未自動更新至子目錄 |
| 7 | Task C：分析 P02 失敗原因，更新 README | 撰寫失敗機制（blooming / 亮部細節流失）與改善方案 | 人工審閱技術說明正確性 | — |
| 8 | 實作 task_c.m，輸出 5 種方法影像與量化指標 | 生成完整 task_c.m，含 HCR、LocalStd 指標 | `matlab -batch` 執行確認 | — |

---

## 詳細對話紀錄

### 1. Task A — 圖像診斷與數據分析

**Prompt**
> 請你閱讀作業說明檔案 project.pdf，理解 TaskA 的實作內容後完善 README.md 的 ## 1. 圖像診斷與數據分析。接著實作 matlab 程式 task_a.m，執行起來給我看看。

**AI Output（概述）**
- 讀取 project.pdf 取得規格
- 生成 `task_a.m`：用迴圈對 5 張圖計算 Mean/Std/RGB mean，再逐張繪製灰階直方圖並以 `saveas` 存 PNG
- 更新 README Task A 統計結果表格與直方圖觀察

**遇到的問題與修正**
- **問題**：T01 是灰階 JPG（1 通道），`rgb2gray` 收到單通道影像時報錯 `Colormap must be a c-by-3 matrix`
- **修正**：AI 加入 `if size(img,3)==3; gray=rgb2gray(img); else; gray=img; end` 判斷

**MATLAB 執行輸出**
```
Image      Mean      Std      R_Mean    G_Mean    B_Mean
{'P01'}    100.42    80.50    100.11    101.06    98.15
{'P02'}     47.87    33.27     46.11     48.33    50.02
{'P03'}     76.16    54.89     99.10     72.93    32.54
{'T01'}     73.04    61.69     73.04     73.04    73.04
{'T02'}    166.95    18.74    199.96    161.42   108.85
```

**驗證**
- 執行 `matlab -batch "run('task_a.m')"` 成功，數值與目視觀察一致（P02 明顯偏暗、P03 R-B 差距最大）

---

### 2. Task B — 方法比較與 IPT 安裝問題

**Prompt**
> 那接下來請你完成 task b，並更新 README.md 的 ## 2. 方法比較與權衡分析部分。

**AI Output（概述）**
- 生成 `task_b.m` 三段（P01 Gamma vs Global HE、P02 Global HE vs CLAHE、P03 RGB 灰世界 vs YCbCr）
- 每段計算統計、印 fprintf 表、存 `tiledlayout` 比較圖

**遇到的問題與修正**

*第一輪：IPT 未安裝*
- **問題**：`histeq` 未定義，因為 Image Processing Toolbox 授權存在但 toolbox 未安裝
- **AI 第一步**：嘗試 `matlab.addons.install` → 失敗（需要互動式 GUI）
- **AI 第二步**：手動實作 `histeq_m`（CDF 映射）、`clahe_m`（分塊等化 + 雙線性插值）、`rgb2ycbcr_m`、`ycbcr2rgb_m`
- **手動 CLAHE 的 bug**：插值索引計算偏移，導致亮暗交界有格狀偽影；AI 修正線性索引公式 `idx11 = bin + N*(ti1-1) + N*nr*(tj1-1)`

*第二輪：安裝 IPT 後*
- 使用者透過 MATLAB GUI 安裝 IPT，AI 將手動實作版本簡化回官方函式版本
- `sprintf` 中 `\gamma` 未逸出導致警告，修正為 `\\gamma`

**AI 缺失**
- 沒有預先用 `license('test','Image_Toolbox')` 偵測 IPT 是否可用，直接假設環境已備妥
- 手動 CLAHE 實作第一版有索引偏移錯誤，需要第二輪 debug

---

### 3. Task B — 補充 RGB 通道欄位與 Trade-off 分析

**Prompt**
> 請你在紀錄 Task B 的時候也要提供 R-mean, G-mean, B-mean, |R-B|，以及各自的優缺點和是否採用。在 README.md 紀錄的時候記得描述 task b 的 trade-off。

**AI Output（概述）**
- 在 `task_b.m` 的 `fprintf` 加入 R/G/B/|R-B| 欄位
- 更新 README Task B 三組表格，加入 R/G/B/|R-B|/採用（✅❌）欄
- 新增三個 Trade-off 分析對照表（優點/缺點並列）、各方法選擇理由段落

**MATLAB 執行輸出**
```
=== P01 統計比較 ===
方法                  Mean   Std    R      G      B     |R-B|
原始                  100.4   80.5  100.1  101.1   98.1    2.0
Gamma γ=0.5           141.3   74.7  140.1  142.5  138.7    1.4
Global HE             118.4   73.1  117.6  119.4  114.7    2.9

=== P02 統計比較 ===
方法                  Mean   Std    R      G      B     |R-B|
原始                   47.9   33.3   46.1   48.3   50.0    3.9
Global HE             113.7   62.3  110.0  114.7  119.0    9.0
CLAHE                  82.8   44.0   81.4   83.3   83.9    2.6

=== P03 統計比較 ===
方法                  Mean   Std    R      G      B     |R-B|
原始                   76.2   54.9   99.1   72.9   32.5   66.6
RGB灰世界              67.6   49.5   68.2   68.2   63.4    4.7
YCbCr                  76.2   54.6   76.9   75.7   76.7    0.3
```

**驗證**
- P01 Gamma |R-B|=1.4（色彩最中性，優於 Global HE 的 2.9）
- P03 YCbCr |R-B|=0.3（近乎完美色彩校正，且 Mean 維持 76.2 不變）

---

### 4. Task B — 輸出個別增強圖片

**Prompt**
> 在 task b 的部分因為作業報告有要求要貼上經過處理的圖，所以你需要把經過影像增強的圖片分別導出到 output/task_b 底下，格式是 b1-1.png, b1-2.png 這種。

**AI Output（概述）**
- 在 `task_b.m` 加入 `if ~exist('output/task_b','dir'); mkdir(...); end`
- 三個 section 末尾分別加入 `imwrite` 存檔：
  - b1-1.png（P01 Gamma）、b1-2.png（P01 Global HE）
  - b2-1.png（P02 Global HE）、b2-2.png（P02 CLAHE）
  - b3-1.png（P03 RGB 灰世界）、b3-2.png（P03 YCbCr）
- 並把 `saveas` 路徑同步改為 `output/task_b/P0X_comparison.png`

**驗證**
- 執行後 `output/task_b/` 存在 9 個 PNG（6 張個別增強圖 + 3 張對比圖）

---

### 5. Task C — 失敗案例分析（README 撰寫）

**Prompt**
> 那接下來進行 task c，我覺得 P02 在 task b 的影像增強表現不好，照片中簡報區域中有流程圖，其白色框線因為影像增強的關係有點暈開（CLAHE），甚至 GLOBAL HE 方法讓整個畫面變亮但是簡報區域感覺變很亮（類似過曝？）。所以請你撰寫失敗條件描述、失敗機制分析、改善或替代方案於 README.md 的 ## 3. 失敗案例分析處。

**AI Output（概述）**
- 失敗條件描述：CLAHE blooming（框線暈開）vs Global HE 亮部細節流失
- 失敗機制分析：
  - CLAHE：8×8 tile 邊界雙線性插值 + 鄰 tile 映射曲線斜率差距大 → 邊緣暈散
  - Global HE：全圖 CDF 強制均布 → 亮投影像素被壓縮至更窄亮帶，LocalStd 降低
- 改善方案表格：降低 ClipLimit、細化 NumTiles、亮部遮罩保護、改用 Gamma

**驗證**
- 技術說明由使用者人工審閱確認正確

---

### 6. Task C — 實作 task_c.m

**Prompt**
> 那請你實作 task_c.m 來改善，同樣把處理後圖片輸出到 output/task_c/，數據要有 Mean, Std, Highlight Clip Ratio, 局部區域 Std。

**AI Output（概述）**
- 建立 `task_c.m`，比較 5 種方法：
  - 原始 / Global HE（失敗A）/ CLAHE 0.02+[8×8]（失敗B）/ Gamma γ=0.6（改善A）/ CLAHE 0.005+[16×16]（改善B）
- 指標定義：
  - **HCR**（Highlight Clip Ratio）：灰階值 ≥ 240 的像素佔比（%）
  - **LocalStd**：以原始 V > 0.65 遮罩界定「簡報投影區域」，計算處理後影像在此區域的灰階 std
- 輸出 `comparison.png` 對比圖（2×5 格）與 5 張個別結果圖

**MATLAB 執行輸出**
```
=== P02 失敗案例分析 ===
方法                        Mean   Std   HCR%  LocalStd
原始                         47.9   33.3   0.1    46.1
Global HE [失敗A]            113.7   62.3   0.2    35.4
CLAHE 0.02 [失敗B]            82.8   44.0   0.1    46.1
Gamma 0.6 [改善A]             85.9   31.0   0.1    40.9
CLAHE 0.005 [改善B]           58.3   35.4   0.1    47.3
```

**驗證**
- `matlab -batch "run('task_c.m')"` exit code 0，`output/task_c/` 存在 6 個 PNG
- Global HE 的 LocalStd 46.1 → 35.4（下降）量化驗證了「亮部細節流失」的論點
- CLAHE 0.005+[16×16] 的 LocalStd=47.3 略高於原始，確認改善效果

---

## AI 工具的缺失與限制

1. **環境假設過於樂觀**：未優先偵測 IPT 是否安裝（如 `license('test','Image_Toolbox')`），直接呼叫 `histeq` 導致執行期錯誤，需額外一輪排錯
2. **手動 CLAHE 索引 bug**：自行實作的雙線性插值第一版有索引偏移，產生格狀偽影；需使用者回報後才發現並修正，顯示 AI 生成演算法程式碼仍需實際執行驗證
3. **編碼顯示問題**：MATLAB batch 模式下中文字元顯示為亂碼（終端機 cp950 與 UTF-8 不一致），AI 未預先提示此限制；實際數值計算不受影響
4. **無法自行執行驗證**：所有程式碼均需使用者手動觸發 `matlab -batch`，AI 無法直接讀取 MATLAB 執行環境，僅能依賴輸出文字判斷正確性
