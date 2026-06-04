# 血液抹片細胞自動辨識系統 — 設計決策紀錄

> 供撰寫 report.pdf 使用，記錄每個關鍵決策的原因與取捨。

---

## 一、前處理 Pipeline

### 1-1 Adaptive Thresholding（非全域 Otsu）

血液抹片光照不均（vignetting），全域閾值在邊緣區域容易誤判。Adaptive Thresholding 以局部 block 加權均值為基準，對光照不均更穩健。

### 1-2 Block Size 71（非原定 51）

**除錯歷程**：
- block=51 時，二值化結果為**環形**（ring artifact）而非實心細胞圓盤。
- 原因：RBC 雙凹圓盤中央淡色區（pale center）在 block=51 局部窗口中高於局部均值，BINARY_INV 判定為背景 → 形成環形空洞。
- block=71（≈1.7× 細胞直徑）：局部窗口納入更多背景像素，拉高均值，細胞中央也落於均值以下，偵測到更完整的實心細胞區域。

### 1-3 輪廓填充取代 Flood Fill（morph_iter=1）

**Flood Fill 除錯歷程**：
- 理論：從角落 (0,0) 填充背景、取反得封閉洞、再 OR 填補細胞中央。
- Bug：`morph_iter≥2` 時環形膨脹觸及影像角落，(0,0)=255。FloodFill 以 255 為種子不改變任何像素，`holes = bitwise_not(flood)` 反轉整個影像，`bitwise_or(morphed, holes)` = 全白 → watershed 計數歸零。
- 驗證：debug 腳本確認 morph_iter=2 後 corner(0,0)=255，最終結果 100% white。

**改用輪廓填充**：RETR_EXTERNAL 輪廓以 FILLED 方式繪製，對閉合輪廓填充內部，不受角落像素影響。

---

## 二、WBC 分類：HSV 飽和度

**問題歷程**：
- `circularity ≥ 0.6`：WBC 中性球多葉核，圓形度約 0.3–0.5 → 全誤歸 RBC，WBC=0。
- 降低至 0.25：大型 RBC 細胞叢（面積 >3000）也滿足 → WBC 計數暴增至 4–9。

**診斷**：對每個偵測區域計算 HSV 均值：
- WBC（紫色 Giemsa 染色）：mean_saturation ≈ 80–95
- RBC（淡粉色）：mean_saturation ≈ 17–44
- 飽和度間距明顯 → `mean_sat ≥ 70 AND area ≥ 2000` 作為 WBC 條件。

**已知限制**：BloodImage_00002 的 WBC 飽和度 ≈ 44（染色較淡），會漏偵測。

---

## 三、Watershed

- Distance Transform 閾值 = 0.5×max（文獻常用值，實測合理）。
- `ws_binary[labels > 1] = 255`（排除背景標籤 1 和 watershed 邊界 -1）。

---

### 1-4 視覺顯示改用最小外接圓

原始輪廓追蹤環形膜邊緣，顯示為不規則弧形，視覺上難以辨識。
改用 `cv2.minEnclosingCircle` 對每個 watershed 區域畫最小外接圓，每顆細胞顯示為乾淨的圓形輪廓，視覺驗證大幅改善。

---

## 四、分類閾值

| 類別 | 面積 | 其他條件 |
|------|------|---------|
| Platelet | < 300 px² | circularity ≥ 0.5 |
| WBC | ≥ 2000 px² | mean_sat ≥ 70 |
| RBC | 其餘 | — |

---

## 五、5 張圖評估結果

參數（固定）：gaussian_ksize=5, adaptive_block=71, C=2, morph_ksize=5, morph_iter=1

| 影像 | RBC pred/GT | WBC pred/GT | PLT pred/GT |
|------|------------|------------|------------|
| BloodImage_00001 | 14/18 | **1/1 ✓** | 0/0 |
| BloodImage_00002 | 10/15 | 0/1 ✗ | 0/0 |
| BloodImage_00003 | 8/15 | **1/1 ✓** | 0/1 |
| BloodImage_00004 | 11/11 | **1/1 ✓** | 0/1 |
| BloodImage_00005 | 10/18 | 0/1 ✗ | 0/3 |

備註：BCCD GT 為稀疏標注（每張圖僅標注 11–18 顆 RBC，實際可見細胞更多），RBC 誤差部分反映標注不完整。

---

## 六、待改進

1. **RBC 低計數**：相鄰細胞合併後 watershed 無法完全分離。
2. **Platelet 漏偵測**：小型血小板常被形態學操作消除。
3. **Image 2/5 WBC 漏偵測**：染色較淡的 WBC 飽和度低於閾值。
