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

目前版本優先採用「面積 + 圓形度規則」完成可解釋的傳統影像處理 pipeline，避免 Watershed 分割線在部分影像上造成過多誤判或視覺干擾。整體流程如下：

1. 前處理與展示
   - 讀取 BGR 影像後轉為灰階。
   - 使用 Gaussian Blur 降低雜訊。
   - App 中額外顯示 Adaptive Threshold 與 Morphological Closing，滿足前處理流程可視化需求。

2. WBC 偵測
   - 使用灰階低亮度區域搭配紫色 HSV mask 擷取白血球候選。
   - 對候選 mask 做 Morphological Closing 合併細胞核區塊。
   - 以 connected component / contour 面積篩選出 WBC 候選。
   - 因 TXL-PBC 多數圖片只有 1 顆 WBC，目前每張圖保留面積最大的 WBC 候選，降低誤把 RBC 群或雜訊當成 WBC 的機率。

3. RBC 偵測與分類
   - 使用 Hough Circle 找圓形候選，避免只靠 threshold 時相鄰 RBC 黏成大區塊。
   - RBC 分類規則以圓形候選的面積與圓形度為主：
     - 面積約束：`RBC_AREA_MIN <= pi * r^2 <= RBC_AREA_MAX`
     - 圓形度：Hough candidate 本身視為圓形候選，等價於 circularity 通過門檻。
   - 只排除最終 WBC 框附近的 RBC 候選，避免用過多 WBC raw candidates 把紅血球誤刪。

4. PLT 偵測
   - 血小板顏色與 RBC/WBC 碎片重疊較高，簡單 HSV 小面積規則會產生大量 FP。
   - 目前採保守策略，預設不輸出 PLT，避免拉低整體 Precision / F1。
   - 若後續要補強 PLT，可另做高信心紫色小物件規則或分開調整血小板專用門檻。

5. 指標計算
   - Ground Truth 採 YOLO normalized bbox 轉 pixel bbox，並裁切到影像邊界。
   - Prediction 與 Ground Truth 需同類別且 IoU >= 閾值才可配對。
   - 採 greedy one-to-one matching，確保一個 GT 和一個 Prediction 最多只配對一次。
   - 以整個 split 累計 TP / FP / FN，再計算 Precision、Recall、F1。
   - 目前預設 IoU 閾值為 `0.3`，test split 的 micro 指標約為 Precision 81.9%、Recall 61.5%、F1 70.2%。

6. App 視覺化
   - Streamlit App 可選擇 train / val / test 圖片。
   - 「Ground Truth 與預測結果」區塊左邊顯示 Ground Truth，右邊顯示預測結果。
   - 框上文字使用 `GT:WBC`、`GT:RBC`、`Pred:WBC`、`Pred:RBC` 等格式，方便 Demo 時直接比對。

