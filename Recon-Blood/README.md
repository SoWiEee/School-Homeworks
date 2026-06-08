# 血液抹片細胞自動辨識與計數系統

> 影像處理 114-2 ｜ 期末專案

## 一、專案目標

綜合應用本學期所學的影像處理技術（空間域濾波、Adaptive Thresholding、形態學操作、輪廓分析），設計一個能自動處理血液抹片影像的互動式 App，將影像中的細胞與背景分離，並計算各類細胞的數量。

## 二、基本規定

| 項目 | 規定 |
| --- | --- |
| 作業形式 | 個人作業 |
| 資料集 | [TXL-PBC_Dataset（GitHub）](https://github.com/lugan113/TXL-PBC_Dataset) |
| 開發環境 | Python + OpenCV + Streamlit（建議使用 Google Colab） |
| 演算法限制 | 禁止使用深度學習（YOLO、CNN 等） |
| 繳交方式 | Colab 連結（或 `.ipynb` 檔案）+ 現場 Demo |
| Demo 時間 | 每人 3 分鐘 |
| 檔案上傳截止日期 | 第 16 週課程結束前（6/11 11:50 AM） |

請同學依以下指標為主作為演算法評分依據：
- Precision
- Recall
- F1 score

並確保程式能夠選定圖片，同時顯示 Ground Truth 與預測結果(預測框)。
本專案為演算法導向，非深度學習訓練流程，因此同學可直接處理全部 1260 張圖片，不需依 train/val/test 進行模型訓練與驗證。

### 針對指標、參數與資料集說明

Ground Truth(也就是標註答案)：位於資料集的labels中，與images中的圖片檔名一一對應，其中資料格式經過正規化，因此需要額外處理

1 0.750435 0.345217 0.203478 0.248696
類別 x軸中心 y軸中心 寬 高

以下為範例處理，將資料轉化為框，提供結果顯示與IoU計算，同學需自行補全如邊界裁切等。
```
xmin = round((center_x - width / 2) * image_width)
ymin = round((center_y - height / 2) * image_height)
xmax = round((center_x + width / 2) * image_width)
ymax = round((center_y + height / 2) * image_height)
```

IoU：面積交集/面積聯集，程式判斷後須轉化成方框，與資料集的面積進行計算，得出分數，作為是否判斷成功之依據，以下提供範例：
```
#格式為[xmin, ymin, xmax, ymax]
# boxA = [x1A, y1A, x2A, y2A]
# boxB = [x1B, y1B, x2B, y2B]
#左上角交集
x_left = max(x1A, x1B)
y_top = max(y1A, y1B)
#右下角交集
x_right = min(x2A, x2B)
y_bottom = min(y2A, y2B)
#計算交集寬高
intersection_width = max(0, x_right - x_left)
intersection_height = max(0, y_bottom - y_top)
#計算交集面積
intersection_area = intersection_width * intersection_height
#計算各自框的面積
areaA = (x2A - x1A) * (y2A - y1A)
areaB = (x2B - x1B) * (y2B - y1B)
#計算聯集面積
union_area = areaA + areaB - intersection_area
#得到IoU分數
IoU = intersection_area / union_area
```

經由 IoU 判斷後，同學需自行設立IoU閥值，進行類別判斷，得到：
- TP(True Positive, 正確辨識)
- FP(False Positive, 檢測出但該位置無Ground Truth)
- FN(False Negative, 未檢測出來但Ground Truth存在)

一個 Ground Truth 最多只能配對一個 Prediction。一個 Prediction 也最多只能配對一個 Ground Truth。
因此需要做一對一配對，避免多個預測框同時算到同一個 Ground Truth，導致 TP 被重複計算。其中 Prediction 與 Ground Truth 必須是同一個類別，且 IoU 大於設定閾值，才可視為 TP。若類別不同，即使框重疊，也不能算入 TP。

指標說明：
Precision 為精確率，代表預測出來的結果中有多少是真的正確，其公式為 TP/(TP+FP)
Recall 為召回率，說明所有 Ground Truth 中，成功分辨出多少，其公式為 TP/(TP+FN)

於上個公告中說明到，需同時顯示 Groun Truth 與預測結果，其目的是同學能夠有辨識成功的視覺依據，若僅以數字分數分辨是否辨識成功，無法得知是否因為誤差辨識成功等原因。

## 三、評分標準

### ▌ 基本要求（必做）— 60 分

| 評分項目 | 說明 | 配分 |
| --- | --- | --- |
| 影像前處理 Pipeline | 灰階、Gaussian Blur、Adaptive Thresholding、Morphological Closing，各階段於 App 中可視化 | 15 分 |
| 細胞偵測與計數 | 至少正確偵測 1 種細胞（白血球為基本要求）<br>1. 誤差 ±30% 內 → 25 分<br>2. 誤差 ±50% 內 → 13 分<br>3. 誤差超過 50% → 0 分 | 25 分 |
| Streamlit App UI | 圖片切換功能、至少 1 個可調參數、各階段結果顯示、下載按鈕 | 10 分 |
| 程式碼品質 | 模組結構清楚、關鍵步驟有中文或英文註解 | 10 分 |

### ▌ 加分挑戰（選做）— 最多 +40 分

| 加分項目 | 說明 | 加分 |
| --- | --- | --- |
| 三種細胞分類 | 以面積 + 圓形度規則分類 RBC / WBC / 血小板並各自計數，每種誤差 ±30% 內 | +15 分 |
| 重疊細胞切分（Watershed） | 使用 Watershed + Distance Transform 成功分離相鄰或重疊的細胞 | +15 分 |
| 5 張圖通用 | 固定參數，在 5 張不同測試圖上不手動調整即可正常運作 | +5 分 |
| 書面報告 | PDF 格式：Pipeline 架構圖、演算法說明、實驗結果表、困難案例分析 | +10 分 |

## 四、分數段對應表現

| 分數 | 對應完成程度 |
| --- | --- |
| 60 分 | 完成前處理 + 各類計數 + 基本 UI，能 Demo |
| 75 分 | 另完成三種細胞分類（面積 + 圓形度規則） |
| 90 分 | 加上 Watershed 切分重疊細胞 |
| 95+ 分 | 再加書面報告 + 5 張圖通用 |

## 五、Demo 與口試說明

每人 3 分鐘，包含：

- 上傳一張血液抹片影像，展示完整處理流程
- 說明設計決策（「為什麼選這個方法」，不只是「我做了什麼」）
- 助教會從問題中了解你對整個 work 的了解有多少

## 實作想法

目前版本優先採用「面積 + 圓形度規則」完成可解釋的傳統影像處理 pipeline，全程不使用任何深度學習。三種細胞各自設計獨立的偵測器，再由 `detect_cells()` 統一輸出方框。

### 專案結構

| 檔案 | 職責 |
| --- | --- |
| `blood_cell_detector.py` | 核心模組：前處理 pipeline、WBC/RBC/PLT 偵測器、Watershed、計數與繪圖工具 |
| `app.py` | Streamlit App：圖片切換、可調參數、各階段視覺化、GT/預測對照、下載按鈕 |
| `txl_pbc_improved_cv.py` | 批次評估腳本：對整個 split 計算 TP/FP/FN 與 Precision/Recall/F1 |
| `et_platelet_model.pkl` | 已訓練的 ExtraTrees 血小板分類器（傳統機器學習，非神經網路） |

### 解析度自適應的尺度基準

所有規則閾值都不是寫死的像素值，而是以**估計的 RBC 半徑 `r0`** 為基準動態縮放（`shape_rbc_radius()`）。`r0` 僅由影像長寬推得（如 575×575 → 65px），不偷看標註答案。如此一來面積、邊界框、最小間距等門檻都能隨影像解析度自動調整，達成「固定參數、多張圖通用」。

### 前處理 Pipeline（`preprocess_pipeline()`）

對應評分項目「影像前處理 Pipeline」，每一階段都在 App 中以圖卡呈現：

```
輸入影像 (BGR)
    ├─ 1. 灰階  cvtColor(BGR2GRAY)
    ├─ 2. Gaussian Blur  高斯模糊去除雜訊（kernel 可調）
    ├─ 3. Adaptive Thresholding  自適應二值化（block size 由 r0 推算，THRESH_BINARY_INV）
    ├─ 4. Morphological Closing  閉運算填補細胞內部破洞
    ├─ 5. Opening Cleanup  開運算清除細小雜點
    ├─ 6. Purple Mask  紫色染色遮罩（供 WBC/PLT 使用）
    └─ 7. Watershed + Distance Transform  重疊細胞切分視覺化
```

### 紫色染色遮罩（關鍵共用元件）

WBC 與血小板的細胞核都被染成紫色，是與粉紅色 RBC 最可靠的區隔。遮罩同時結合 **HSV** 與 **LAB** 兩個色彩空間（`A>145` 偏紅、`B<125` 偏藍 → 紫色），比單一 HSV 更穩定：

- `purple_mask_strict()`：高精確率，用於 WBC 偵測與「把 RBC 排除在紫色區外」。
- `purple_mask_loose()`：高召回率，用於血小板候選抽取（寧可多抓再用分類器過濾）。

### 三種細胞偵測策略

**WBC（`detect_wbc`）**
紫色遮罩 → 膨脹（dilation）把破碎的細胞核碎片合併成一團 → 連通元件分析 → 以「幾何夠大（> 1.05·r0）」且「顏色夠藍/夠飽和」的雙重規則篩出白血球，最後以中心距離做 NMS 去重。

**RBC（`detect_rbc_rule`）**
取前處理後的二值圖 → `findContours` 抽輪廓 → 用**面積、邊界框尺寸、長寬比、圓形度**四道規則篩選（圓形度 `4πA/P²`），並排除落在紫色區內的輪廓（避免把 WBC 算成 RBC）→ 中心距離 NMS。

**血小板（兩種模式）**
- *Rule-based only*（`detect_platelets_rule`）：寬鬆紫色遮罩取小面積連通元件 → 面積/圓形度/顏色規則。
- *Improved classical*（`detect_platelets_ml`，預設）：對每個候選抽取 **55 維手工特徵**（面積比、長寬比、extent、圓形度、solidity、位置、局部紫色比例，以及 H/S/V/L/A/B/灰階 7 個通道的統計量）→ 餵入 **ExtraTreesClassifier** 輸出機率 → 以門檻過濾。這是傳統機器學習，符合「禁用深度學習」規定。

### Watershed + Distance Transform（加分項）

`watershed_rbc_candidates()` / `watershed_visualization()` 針對相鄰、重疊的 RBC：以 Distance Transform 的局部峰值（`peak_local_max`）作為種子標記，再用 Watershed 沿強度谷底切開黏合邊界，於 App 中以紅線疊圖顯示。App 提供勾選框，可把 Watershed 候選**補充**進 RBC 計數；但預設關閉，因為純 Watershed 在此資料集容易過度切分，預設仍以較穩定的 adaptive 輪廓分支為主。

### 評估與配對規則（`txl_pbc_improved_cv.py`）

依公告要求做 **一對一貪婪配對**：對每個類別，預測框中心若落在「同類別」GT 框內（含 15% 邊界容差）即配對，一個 GT 只能配一個預測。據此計算 TP/FP/FN，再得出 Precision = TP/(TP+FP)、Recall = TP/(TP+FN)、F1，並輸出 micro 平均。

### Streamlit App 功能（`app.py`）

對應「Streamlit App UI」評分項目：
- **圖片切換**：側欄選擇 split 與影像。
- **可調參數**：Gaussian kernel、adaptive block ratio、adaptive C、closing kernel、RBC/PLT 圓形度門檻、血小板 ML 門檻、Watershed 開關。
- **各階段顯示**：前處理 7 階段圖卡、GT 與預測雙欄對照、計數誤差表（±30%/±50% PASS/FAIL）。
- **下載按鈕**：預測疊圖 PNG、預測框 CSV、計數誤差 CSV。

### 成果

三種細胞於 test/val/train 三個 split 上的計數誤差均達 **±30%** 標準（詳見 `report.md` 的迭代紀錄）。

