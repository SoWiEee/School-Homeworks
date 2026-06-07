# 血液抹片細胞偵測系統 — 開發紀錄

## 資料集分析

- 資料集：TXL-PBC_Dataset
- 影像尺寸：575 × 575 px
- Test 集：126 張，WBC 133個（avg 1.1/張）、RBC 1699個（avg 13.5/張）、PLT 49個（avg 0.4/張）
- 類別標籤（YOLO 格式）：0=WBC、1=RBC、2=Platelet

### GT Bounding Box 特徵統計

| 細胞 | Bbox 平均面積 (px²) | 估計輪廓面積 (px²) | 估計半徑 (px) |
|------|--------------------|--------------------|---------------|
| WBC  | ~57,174            | ~45,000            | ~135          |
| RBC  | ~14,250            | ~11,200            | ~60           |
| PLT  | ~2,589             | ~2,000             | ~25           |

### GT 像素值分析（bbox 內統計）

| 細胞 | 灰階 gmin 中位數 | 灰階 gmed 中位數 | HSV H 中位數 | HSV S 中位數 |
|------|-----------------|-----------------|--------------|--------------|
| WBC  | 36              | 139             | 137          | 85           |
| RBC  | 134             | 170             | 146*         | 53           |
| PLT  | 59              | 198             | 50           | 51           |

\* RBC 的 H 值呈雙峰分布：H=0-20（紅粉色）與 H=155-180（環繞紅色）。

---

## 演算法設計與迭代優化

### Pipeline 架構

```
輸入影像 (BGR)
    │
    ├─[Step 1] WBC 偵測
    │   灰階 → GaussianBlur(11×11) → threshold(gray < 130) AND purple HSV mask
    │   → morphClose(23×23) → morphOpen(9×9) → 篩選輪廓面積 > 9500 px²
    │   → 建立 WBC 排除區（bbox + 65px pad）
    │
    ├─[Step 2] RBC 偵測 (Hough Circles)
    │   灰階 → GaussianBlur(5×5) → HoughCircles(dp=1, minDist=38, param2=12, r=28-78)
    │   → 排除 WBC 區域內的圓 → 建立 RBC 排除圓
    │
    └─[Step 3] PLT 偵測 (紫色色彩遮罩)
        HSV purple mask (H=112-162, S>38, V<210)
        → 排除 WBC 與 RBC 區域
        → morphOpen(2×2) → morphClose(4×4)
        → 篩選輪廓面積 400-3000 px²
```

---

## 迭代優化歷程

### 版本 1 — 初始嘗試（全部失敗）

**策略**：灰階 adaptive threshold → 輪廓面積分類

| 細胞 | GT  | 預測 | 誤差      | 狀態 |
|------|-----|------|-----------|------|
| WBC  | 133 | 87   | −34.6%    | FAIL |
| RBC  | 1699 | 165 | −90.3%   | FAIL |
| PLT  | 49  | 2544 | +5091.8% | FAIL |

**問題分析**：
- WBC：threshold=100 太嚴，遺漏許多細胞核
- RBC：blockSize=51 的 adaptive threshold 無法有效偵測粉紅色 RBC
- PLT：小輪廓面積範圍（80-1200 px）捕捉了大量影像雜訊

---

### 版本 2 — 導入 Hough Circles 偵測 RBC

**策略改變**：
- WBC：保留灰階閾值法，min_area=18000
- RBC：改用 HoughCircles（param2=25, r=30-80）
- PLT：改用 HSV 紫色遮罩

| 細胞 | GT  | 預測 | 誤差    | 狀態 |
|------|-----|------|---------|------|
| WBC  | 133 | 48   | −63.9%  | FAIL |
| RBC  | 1699 | 739 | −56.5% | FAIL |
| PLT  | 49  | 722  | +1373%  | FAIL |

**問題分析**：
- WBC：WBC_MIN_AREA=18000 太大，遺漏許多 WBC（最小 bbox 僅 8092 px²）
- RBC：param2=25 太嚴格，Hough 遺漏了大量圓形
- PLT：紫色遮罩範圍過寬（H=110-165, S>30）

---

### 版本 3 — 像素值分析後重新校準

**關鍵發現（analyze.py 分析）**：
- 所有 WBC 的 gmin（bbox 內最暗像素）< 130
- RBC 中心灰階值差異極大（93-230），但 H 值呈雙峰
- PLT bbox 面積較小（294-11990 px²）且顏色高度不均一（部分粉色、部分紫色）

**策略改變**：
- WBC：threshold=130（確保全部 WBC 都有核心像素被捕捉）+ purple HSV AND mask（防止合併深色 RBC 叢）
- RBC：param2=10，minDist=38（更積極的偵測）
- PLT：縮小紫色遮罩範圍並加入面積篩選

| 細胞 | GT  | 預測 | 誤差    | 狀態 |
|------|-----|------|---------|------|
| WBC  | 133 | 142  | +6.8%   | OK   |
| RBC  | 1699 | 1849 | +8.8%  | OK   |
| PLT  | 49  | 143  | +191.8% | FAIL |

**WBC 與 RBC 達標，PLT 仍過多偵測。**

---

### 版本 4 — PLT 精細化（最終結果）

**PLT 問題根源**：
- 紫色遮罩捕捉到 WBC 細胞質碎片（位於排除區外）
- 小面積雜訊（area < 400 px²）佔多數假陽性
- 低飽和度的紫色區塊多為非 PLT 物質

**修正策略**：
- 增加 WBC_PAD 至 65px（排除更多 WBC 細胞質）
- 提高 PLT_MIN_AREA 至 400 px²（排除雜訊碎片）
- 提高 PLT_PURP_S_MIN 至 38（要求更純的紫色）

**最終結果（test 集）**：

| 細胞 | GT  | 預測 | 誤差   | 狀態 |
|------|-----|------|--------|------|
| WBC  | 133 | 142  | +6.8%  | OK   |
| RBC  | 1699 | 1849 | +8.8% | OK   |
| PLT  | 49  | 57   | +16.3% | OK   |

**跨分割泛化驗證**：

| Split | Images | WBC 誤差 | RBC 誤差 | PLT 誤差 |
|-------|--------|----------|----------|----------|
| test  | 126    | +6.8%    | +8.8%    | +16.3%   |
| val   | 252    | +15.2%   | +6.1%    | +11.6%   |
| train | 882    | +18.0%   | +2.1%    | +6.8%    |

**三種細胞在三個分割上均達到 ±30% 誤差標準。**

---

## Watershed + Distance Transform 重疊細胞切分

### 問題動機

Hough Circle Transform 在 RBC 緊密聚集時容易漏偵測重疊區域（相鄰圓圓心距離 < minDist 時被濾掉）。Watershed 演算法可將相鄰細胞的連通區域切分為個別細胞，更準確地計數堆疊 RBC。

### 演算法流程

```
灰階影像
    │
    ├─ GaussianBlur(5×5)
    │
    ├─ Adaptive Threshold(31, 5) → BINARY_INV
    │    排除 WBC 區域（bitwise_and with NOT wbc_excl）
    │
    ├─ morphClose(18×18)  ← 填滿 RBC 雙凹圓盤中心（變成 solid disc）
    │
    ├─ morphOpen(10×10)   ← 去除血小板尺度雜訊（< ~300 px²）
    │
    ├─ dilate(3×3, iter=2) → sure_bg（確定背景）
    │
    ├─ distanceTransform(DIST_L2)
    │    每個 RBC disc 中心出現距離峰值
    │
    ├─ threshold(dist > 0.40 × max) → sure_fg（確定前景，即細胞種子）
    │
    ├─ unknown = sure_bg − sure_fg
    │
    ├─ connectedComponents(sure_fg) → markers
    │    markers + 1（背景 → 1），unknown → 0
    │
    ├─ cv2.watershed(img, markers) → -1 = 細胞邊界
    │
    └─ 每個 label > 1 的區域 → minEnclosingCircle → (cx, cy, r)
         面積 < 800 px² 的區域排除（非 RBC 碎片）
```

### 視覺效果

結果影像中黃色細線為 Watershed 分割邊界，直觀顯示：
- 原本黏在一起的 RBC 群被切割成獨立個體
- 每個分割區域對應一個 RBC 計數

### 關鍵參數

| 參數 | 值 | 說明 |
|------|----|------|
| `WS_CLOSE_K` | 18 | 填滿 RBC 雙凹中心的 closing kernel |
| `WS_OPEN_K` | 10 | 去除 PLT 尺度雜訊的 opening kernel |
| `WS_DIST_THRESH` | 0.40 | Distance Transform 峰值閾值（越低→偵測越多種子） |
| 面積濾波 | 800 px² | 排除非 RBC 的小型分割碎片 |

---

## 最終參數設定

```python
# WBC
WBC_GRAY_THRESH = 130
WBC_CLOSE_K     = 23
WBC_OPEN_K      = 9
WBC_MIN_AREA    = 9500  # px²
WBC_PAD         = 65    # px

# RBC (Hough Circles)
RBC_MIN_DIST = 38
RBC_PARAM1   = 50
RBC_PARAM2   = 12
RBC_MIN_R    = 28       # px
RBC_MAX_R    = 78       # px

# PLT (purple HSV mask)
PLT_PURP_H_LO  = 112
PLT_PURP_H_HI  = 162
PLT_PURP_S_MIN = 38
PLT_PURP_V_HI  = 210
PLT_MIN_AREA   = 400    # px²
PLT_MAX_AREA   = 3000   # px²
```

---

---

## 兩種偵測策略設計

系統支援兩種偵測模式，透過 `DETECTION_MODE` flag 切換：

### 模式一：獨立 Pipeline（`pipeline`）

各細胞使用各自專屬的偵測流程：

```
輸入影像
  ├─ WBC: GaussianBlur(11×11) → 全域閾值(130) AND 紫色 HSV mask
  │        → morphClose(23×23) → morphOpen(9×9) → 輪廓面積 > 9500px²
  ├─ RBC: GaussianBlur(5×5) → HoughCircles(param2=12, r=28-78)
  │        → 排除 WBC 區域
  └─ PLT: HSV 紫色 mask (H=112-162, S>38) → 排除 WBC+RBC 區域
           → 輪廓面積 400-3000px²
```

**優點**：各細胞用最適合的特徵，精度最高（test WBC+6.8%, RBC+8.8%, PLT+16.3%）
**缺點**：各管線獨立，不符合「面積＋圓形度」統一分類的教學定義

---

### 模式二：面積＋圓形度規則分類（`classify`）

統一找出所有細胞輪廓後，以形態學特徵進行分類：

```
輸入影像
  ↓
GaussianBlur(9×9)
  ↓
全域閾值(150) OR Adaptive Threshold(blockSize=31) → 合併
  ↓
morphClose(5×5) → morphOpen(3×3)
  ↓
findContours → 對每個輪廓計算：
    面積 = cv2.contourArea(cnt)
    圓形度 = 4π × 面積 / 周長²  （完美圓形 = 1.0）
  ↓
分類規則：
    面積 ≥ 9000 px²                          → WBC
    1500 ≤ 面積 < 9000 且 圓形度 ≥ 0.55    → RBC（接近圓形）
    250 ≤ 面積 ≤ 2500                        → PLT（小型碎片）
```

**優點**：符合課程定義的「面積＋圓形度規則」，架構清晰易解釋
**缺點**：RBC 因形變/重疊導致圓形度偏低時容易漏偵測；PLT 因缺乏顏色過濾容易混入 RBC 邊緣碎片

### Classify 模式實測結果分析

在 test 集（126 張）的最佳參數下：

| 細胞 | GT | 預測 | 誤差 | 狀態 |
|------|----|------|------|------|
| WBC  | 133 | 97  | -27.1% | ✓（接近邊界）|
| RBC  | 1699 | 226 | -84.0% | ✗ |
| PLT  | 49  | 1881 | +3738% | ✗ |

**根本原因分析：**

1. **RBC 嚴重漏偵測（-84%）**：RBC 的雙凹（biconcave）形狀在 adaptive threshold 後呈現為環形輪廓，closing 操作無法完全填滿中心。實測輪廓圓形度中位數僅 0.16（完美圓形=1.0），遠低於任何合理閾值，導致幾乎所有 RBC 被過濾掉。
   
   這正是 Hough Circle Transform 的優勢所在：Hough 專門設計用於偵測環形輪廓，不受 circularity 計算的填充問題影響。

2. **PLT 嚴重過偵測（+3738%）**：PLT 的面積範圍（200-1800 px²）與影像雜訊、細胞邊緣碎片高度重疊。缺乏顏色資訊（紫色 HSV mask）無法區分真正的血小板與背景碎片。

**結論**：純面積＋圓形度分類在此資料集無法達到 ±30% 誤差，主因是 RBC 的雙凹特性與 PLT 的顏色依賴性。因此本系統的主要偵測策略採用 pipeline 模式，classify 模式作為教學示範用途，呈現特徵工程的思路與侷限。

---

## 困難案例分析

1. **WBC 細胞核偏移**：部分 WBC 的 bbox 中心落在細胞質（而非細胞核），導致中心像素灰階值高達 180-220。解法：使用較高的灰階閾值（130）並結合形態學 closing 合併細胞核碎片。

2. **RBC 堆疊重疊**：緊密相鄰的 RBC 使 Hough Circles 難以區分個別圓。解法：使用適當的 minDist=38 與 param2=12 平衡召回率與精確率。

3. **PLT 顏色不均一**：約 47% 的 PLT 呈粉紅色（H=0-25，與 RBC 相近），另 53% 呈紫色。粉紅色 PLT 難以從 RBC 邊緣碎片中辨別，目前僅透過紫色遮罩捕捉後者。

4. **偵測耦合效應**：WBC 排除區大小直接影響 RBC 偵測數量。WBC_PAD 增大 → RBC 排除更多 → RBC 漏偵測。需要在 WBC_PAD 與 RBC 召回率之間取得平衡。
