# TXL-PBC 血液抹片細胞偵測報告

> 影像處理 114-2 ｜ 期末專案書面報告
> 一個不使用深度學習的血液抹片細胞計數 Streamlit App。

本報告與目前程式碼（`blood_cell_detector.py`、`app.py`、`txl_pbc_improved_cv.py`）同步，
實驗數據由 `txl_pbc_improved_cv.py` 實際執行重現（見第三節）。

---

## 一、Pipeline 架構

```
輸入 RGB 影像
    │
    ├─ 灰階 Grayscale
    ├─ 高斯模糊 Gaussian Blur
    ├─ 自適應二值化 Adaptive Thresholding
    ├─ 形態學閉運算 + 開運算 Morphological Closing & Opening
    ├─ 輪廓抽取 Contour extraction
    ├─ 面積 / 圓形度 / 長寬比 / 顏色 規則篩選
    ├─（選用）Distance Transform + Watershed
    └─ 計數 WBC / RBC / Platelet 並繪製方框
```

所有尺寸門檻都以「由影像解析度估計的 RBC 半徑 `r0`」為基準動態縮放
（`shape_rbc_radius()`，例如 575×575 → `r0=65px`），不偷看標註答案，
因此固定參數即可在不同解析度影像上通用。

---

## 二、演算法摘要

### WBC 偵測（`detect_wbc`）

將影像轉到 **HSV 與 LAB** 兩個色彩空間，分割出被染成紫／紫羅蘭色的細胞核區域
（`A>145` 偏紅、`B<125` 偏藍 → 紫色），以膨脹（dilation）把破碎的細胞核合併成一團，
再用「幾何夠大（邊界框 > 1.05·r0）」與「顏色統計（夠藍/夠飽和）」雙重規則篩選候選，
最後以中心距離 NMS 去重。

### RBC 偵測（`detect_rbc_rule` / `detect_rbc_adaptive`）

灰階 → 高斯模糊 → 自適應二值化（block size 由 `r0` 推算）→ 形態學閉/開運算 →
`findContours` 抽輪廓，再用**面積、圓形度（4πA/P²）、長寬比、以及由解析度推得的 RBC 半徑**
四道規則篩選；同時排除中心落在紫色區內的輪廓，避免把 WBC 誤判成 RBC。

### 血小板偵測（兩種模式）

- **Rule-only**（`detect_platelets_rule`）：以寬鬆紫色遮罩取小面積連通元件，
  再用面積 / 圓形度 / 顏色規則篩選。
- **Improved classical**（`detect_platelets_ml`，預設）：使用相同的高召回候選抽取，
  接著對每個候選抽取 **手工特徵**（形狀、顏色、局部脈絡：面積比、長寬比、extent、
  圓形度、solidity、位置、局部紫色比例，以及 H/S/V/L/A/B/灰階 7 通道統計量），
  餵入 **ExtraTreesClassifier** 輸出機率後以門檻過濾。
  這是傳統機器學習，**不使用 CNN、YOLO、U-Net 或任何神經網路**。

### Watershed（重疊細胞切分，加分項）

由前景遮罩計算 Distance Transform，取局部峰值作為 marker，再以 watershed 分割切開
相鄰、黏合的 RBC 區域。Streamlit App 會顯示此階段，並可選擇將 watershed 候選
補充進 RBC 計數（預設關閉，因純 watershed 在此資料集容易過度切分）。

---

## 三、實驗結果

評估規則（`txl_pbc_improved_cv.py`）：採一對一貪婪配對，預測框中心落在「同類別」
GT 框內（含 15% 邊界容差）即視為 TP，一個 GT 只能配一個預測。

### Test 集（126 張，improved classical 模式）

| 類別 | TP | FP | FN | Precision | Recall | F1 |
|------|----|----|----|-----------|--------|------|
| WBC       | 104  | 8   | 29  | 92.86% | 78.20% | 84.90% |
| RBC       | 1200 | 428 | 499 | 73.71% | 70.63% | 72.14% |
| Platelet  | 43   | 2   | 6   | 95.56% | 87.76% | 91.49% |
| **micro** | 1347 | 438 | 534 | 75.46% | 71.61% | 73.49% |

三個類別在 test 集的 Precision、Recall、F1 皆達 70% 門檻。

### Val 集（252 張，improved classical 模式）

| 類別 | TP | FP | FN | Precision | Recall | F1 |
|------|----|----|----|-----------|--------|------|
| WBC       | 213  | 31  | 44  | 87.30% | 82.88% | 85.03% |
| RBC       | 2545 | 882 | 838 | 74.26% | 75.23% | 74.74% |
| Platelet  | 93   | 9   | 19  | 91.18% | 83.04% | 86.92% |
| **micro** | 2851 | 922 | 901 | 75.56% | 75.99% | 75.77% |

### 重現方式

```bash
python txl_pbc_improved_cv.py --root TXL-PBC_Dataset/TXL-PBC \
    --split test --platelet-model et_platelet_model.pkl
```

> 以上數據已於本機實際執行重現，與 `reports/test_metrics.csv`、`reports/val_metrics.csv` 一致。

---

## 四、範例疊圖

`reports/TXL_PBC_Classical_CV_Report.pdf` 第 4 節提供一張範例疊圖
（亦見 `assets/overlay_example.jpg`）：

- 綠框 / 紅框 / 藍框：RBC、Platelet、WBC 的 Ground Truth。
- App 中以 `GT:WBC`、`Pred:WBC` 形式同時標註 GT 與預測，提供辨識成功的視覺依據。

---

## 五、困難案例與限制

| 案例 | 困難點 | 本專案的緩解方式 |
|------|--------|------------------|
| RBC 重疊 | 輪廓合併成一大塊，純面積計數會低估細胞數 | 提供 Distance Transform + Watershed 作為視覺化與選用的計數補充 |
| 血小板貼近 WBC 核 | 小型紫色元件易與 WBC 細胞核碎片混淆 | improved classical 模式用局部脈絡手工特徵 + ExtraTrees 分類 |
| 染色變異 | 固定 HSV/LAB 門檻可能漏掉淡染細胞或誤收染色雜質 | 同時使用 HSV 與 LAB 規則，並透過 UI 參數間接調整門檻 |
| 標註模糊 | 部分小紫色元件外觀像血小板但未被標註 | 並排顯示 GT 與預測，讓假陽性在 Demo 時清楚可見 |

---

## 六、Streamlit App UI 檢查表

| 要求 | 在 App 中的位置 |
|------|-----------------|
| train / val / test 影像選擇 | 側欄 split 選擇器與影像下拉選單 |
| Ground Truth vs Prediction | 並排面板，標籤採 `GT:WBC`、`Pred:RBC` 形式 |
| 至少一個可調參數 | Gaussian kernel、adaptive C、closing kernel、圓形度門檻、血小板門檻 |
| Pipeline 視覺化 | 主頁 pipeline 區塊顯示灰階、高斯模糊、自適應二值化、形態學閉運算等 |
| 下載按鈕 | 疊圖 PNG、預測框 CSV、計數誤差 CSV |

---

## 七、建議 Demo 流程

1. 選擇 test split 與下拉選單中的一張影像。
2. 展示 pipeline 區塊，指出灰階、高斯模糊、自適應二值化、形態學閉運算各階段。
3. 展示並排的 Ground Truth 與 Prediction 面板，確認標籤為 `GT:WBC`、`Pred:WBC` 形式。
4. 在較擁擠的影像上勾選 Watershed RBC supplementation，示範重疊細胞切分。
5. 下載疊圖 PNG 或 CSV，示範匯出功能。
