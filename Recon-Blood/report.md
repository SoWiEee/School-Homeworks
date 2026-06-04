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

## 二、三種獨立偵測策略（第二版重構）

前一版以 Watershed 輪廓 + 面積/飽和度統一分類，存在以下問題：
- WBC 多葉核被 Watershed 切成多個小區域，mean_sat 計算失真
- RBC 計數依賴 Watershed 分離效果，相鄰細胞常合併計一
- Platelet 被形態學操作消除，幾乎全數漏偵測

重構後每類細胞採用最適策略：

### 2-1 WBC：HSV 紫色遮罩 + 形態學聚合 + 凸包

1. `inRange(hsv, (100,60,50), (170,255,210))`：提取 Giemsa 藍紫色核
2. `dilate(kernel=15) + close(kernel=15)`：合併多葉核碎片為整塊
3. 距離 < 140px 的連通域聚類，合併為同一 WBC
4. 取凸包，選取最大非邊界候選（area ≥ 6000px²）
5. 若無非邊界候選，接受邊界候選（partial_wbc_border）

**優點**：不依賴 Watershed，對多葉核完全合併，鑑別能力強。

### 2-2 RBC：CLAHE + Hough 圓形偵測 + 雙通道顏色驗證

1. **CLAHE 影像增強**：局部直方圖均衡化（clipLimit=2.0, tileGridSize=8×8），提升染色不均區域對比
2. Median Blur(5)：抑制雜訊同時保留邊緣
3. HoughCircles(dp=1.2, minDist=35, param1=50, param2=28, r=18–55)
4. 雙通道顏色驗證（以下任一通過即計入）：
   - HSV：`(H≥150 or H≤10) and S:8–100 and V:100–240`（粉紅/紅色）
   - Lab：`A≥132 and B≥118 and L:110–225`（正向色度）
5. WBC 排除：圓圈區域內 WBC 像素佔比 > 8% 則剔除
6. 顏色驗證：圓圈區域內 RBC 色像素佔比 < 15% 則剔除

**優點**：Hough 天然適合圓形細胞；CLAHE 改善淡染漏偵測；顏色驗證排除誤報。

### 2-3 Platelet：HSV 紫色小物件 + WBC 積極排除

1. `inRange(hsv, (110,80,30), (160,255,210))`：較窄範圍，排除淡紫色背景
2. WBC 所在區域膨脹 35px 後完全遮蔽，消除 WBC 核碎片干擾
3. 篩選條件：面積 8–250px²、長寬比 0.35–2.8、圓形度 ≥ 0.2、不觸及邊界

---

## 三、影像增強：CLAHE

CLAHE（Contrast Limited Adaptive Histogram Equalization）用於改善血液抹片染色不均問題：
- 全域直方圖均衡化（HE）會過度增強亮區雜訊；CLAHE 以局部 tile 為單位，clipLimit 限制對比放大倍率
- 應用於 RBC Hough 偵測前的灰階預處理，使淡染細胞與背景對比提升
- 同時加入前處理視覺化 pipeline，供 Streamlit App Pipeline 分頁展示

---

## 四、Watershed（視覺化保留）

- 保留 Watershed 用於 Streamlit App Tab 3 視覺化展示及評分項目
- Distance Transform 閾值 = 0.5×max
- 不再作為 RBC/WBC/Platelet 計數依據

---

## 五、5 張圖評估結果（第二版，需 Colab 執行確認）

參數（固定）：gaussian_ksize=5, adaptive_block=71, C=2, morph_ksize=5, morph_iter=1, Hough param2=28

| 影像 | RBC pred/GT | WBC pred/GT | PLT pred/GT |
|------|------------|------------|------------|
| BloodImage_00001 | TBD/18 | TBD/1 | TBD/0 |
| BloodImage_00002 | TBD/15 | TBD/1 | TBD/0 |
| BloodImage_00003 | TBD/15 | TBD/1 | TBD/1 |
| BloodImage_00004 | TBD/11 | TBD/1 | TBD/1 |
| BloodImage_00005 | TBD/18 | TBD/1 | TBD/3 |

備註：BCCD GT 為稀疏標注，RBC 誤差部分反映標注不完整。執行 §7 後填入實際數字。

---

## 六、待改進

1. **Hough param2**：固定 28 對不同圖片靈敏度略有差異。
2. **Image 2/5 WBC**：染色較淡仍可能漏偵測，需人工確認。
3. **Platelet 計數**：保守設計減少誤報，但仍可能漏偵較暗血小板。
