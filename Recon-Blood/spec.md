# 實作規格：血液抹片細胞自動辨識與計數系統

> 影像處理 114-2 ｜ 期末專案 ｜ 目標 95+ 分

---

## 一、整體架構

採用**單一 Colab Notebook（方案 A）**，以 cell 區塊分職責，最終透過 `%%writefile` + `pyngrok` 啟動 Streamlit。

```
Final_Project.ipynb
├── §0 Setup           安裝依賴、掛載 BCCD dataset
├── §1 Utils           I/O、視覺化輔助函式
├── §2 Preprocess      前處理 pipeline（4 階段）
├── §3 Detect          輪廓分析與面積過濾
├── §4 Classify        RBC / WBC / Platelet 分類
├── §5 Watershed       重疊細胞切分
├── §6 Pipeline        整合 §2–§5 的總控函式
├── §7 Evaluation      5 張測試圖固定參數評估
└── §8 Streamlit App   %%writefile app.py → pyngrok 啟動
```

---

## 二、環境設定（§0 Setup）

```python
# 安裝套件
!pip install streamlit pyngrok opencv-python-headless

# 掛載 Google Drive 並解壓 BCCD Dataset
from google.colab import drive
drive.mount('/content/drive')
# BCCD dataset 路徑：/content/BCCD/
```

**依賴版本**
| 套件 | 最低版本 |
|------|---------|
| opencv-python-headless | 4.8+ |
| streamlit | 1.30+ |
| pyngrok | 7.0+ |
| numpy | 1.24+ |

---

## 三、輔助函式（§1 Utils）

### `show(title, img)`
顯示影像於 notebook（`cv2.imshow` 不可用，改用 `matplotlib`）。

### `overlay_contours(img, contours_dict) -> np.ndarray`
- 輸入：原圖 BGR、`dict(rbc=[], wbc=[], platelet=[])`
- 輸出：疊加彩色輪廓的 BGR 影像
  - RBC：紅色 `(0, 0, 255)`
  - WBC：綠色 `(0, 255, 0)`
  - Platelet：藍色 `(255, 0, 0)`

### `encode_image(img) -> bytes`
將 BGR 影像壓成 PNG bytes，供 Streamlit 下載按鈕使用。

---

## 四、前處理（§2 Preprocess）

### `preprocess(img, params) -> dict`

**輸入**
- `img`：BGR `np.ndarray`
- `params`：`PreprocessParams`（見下方）

**輸出** — 依序包含各階段影像的 dict：
```python
{
  "original":   np.ndarray,  # BGR
  "gray":       np.ndarray,  # 灰階
  "blurred":    np.ndarray,  # 灰階
  "thresh":     np.ndarray,  # 二值（0/255）
  "morphed":    np.ndarray,  # 二值（0/255）
}
```

**參數結構 `PreprocessParams`**
```python
@dataclass
class PreprocessParams:
    gaussian_ksize: int = 5       # 必須為奇數
    adaptive_block: int = 51      # 必須為奇數，越大越平滑
    adaptive_c:     int = 5       # 從均值減去的常數
    morph_ksize:    int = 3
    morph_iter:     int = 2
```

**Pipeline 步驟**
1. `gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)`
2. `blurred = cv2.GaussianBlur(gray, (ksize, ksize), 0)`
3. `thresh = cv2.adaptiveThreshold(blurred, 255, ADAPTIVE_THRESH_GAUSSIAN_C, THRESH_BINARY_INV, block, C)`
4. `kernel = cv2.getStructuringElement(MORPH_ELLIPSE, (ksize, ksize))`
5. `morphed = cv2.morphologyEx(thresh, MORPH_CLOSE, kernel, iterations=iter)`

---

## 五、細胞偵測（§3 Detect）

### `detect_cells(binary, min_area=50) -> list[dict]`

**輸入**：二值影像（`morphed`）、最小面積閾值

**輸出**：輪廓資訊 list，每項為：
```python
{
  "contour":     np.ndarray,   # cv2 contour
  "area":        float,
  "perimeter":   float,
  "circularity": float,        # 4π·A / P²，範圍 [0, 1]
  "bbox":        tuple,        # (x, y, w, h)
}
```

**步驟**
1. `contours, _ = cv2.findContours(binary, RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)`
2. 過濾 `area < min_area` 的雜訊輪廓
3. 計算每個輪廓的 `area`、`perimeter`、`circularity = 4π·area / perimeter²`

---

## 六、細胞分類（§4 Classify）

### `classify(cells) -> dict`

**輸入**：`detect_cells()` 回傳的 list

**輸出**
```python
{
  "rbc":      [contour, ...],
  "wbc":      [contour, ...],
  "platelet": [contour, ...],
}
```

**分類規則（面積 + 圓形度）**
| 細胞 | 面積範圍（px²） | 圓形度 |
|------|----------------|--------|
| Platelet（血小板） | 50 – 300 | ≥ 0.5 |
| RBC（紅血球） | 300 – 2000 | 任意 |
| WBC（白血球） | > 2000 | ≥ 0.6 |

- 先以面積初篩，再以圓形度細分
- 不符合任何條件的輪廓歸入 `rbc`（最大宗）

---

## 七、Watershed 重疊切分（§5 Watershed）

### `watershed_split(original, binary) -> np.ndarray`

**輸入**：原圖 BGR、`morphed` 二值影像

**輸出**：`labels`（int32 marker map，每個連通域一個 ID）

**步驟**
1. `sure_bg = cv2.dilate(binary, kernel, iterations=3)`
2. `dist = cv2.distanceTransform(binary, DIST_L2, 5)`
3. `_, sure_fg = cv2.threshold(dist, 0.5 * dist.max(), 255, 0)`
4. `unknown = sure_bg - sure_fg`（未確定區域）
5. `_, markers = cv2.connectedComponents(sure_fg.astype(np.uint8))`
6. `markers += 1; markers[unknown == 255] = 0`
7. `cv2.watershed(original, markers)` → 回傳 `markers`

**使用時機**：在 `detect_cells()` 之前先對二值影像做切分，再跑輪廓分析，可分離相鄰 RBC 群聚。

---

## 八、總控 Pipeline（§6 Pipeline）

### `run_pipeline(img, params) -> dict`

**輸入**
- `img`：BGR 影像
- `params`：`PreprocessParams`

**輸出**
```python
{
  "stages":   dict,   # preprocess() 的完整輸出
  "cells":    list,   # detect_cells() 輸出
  "counts":   {       # 各類別數量
                "rbc": int, "wbc": int, "platelet": int
              },
  "overlay":  np.ndarray,  # 標註後的 BGR 影像
  "labels":   np.ndarray,  # watershed markers
}
```

**執行順序**
```
preprocess → watershed_split → detect_cells → classify → overlay_contours
```

---

## 九、固定參數評估（§7 Evaluation）

### `eval_table(pipeline_fn, img_paths, gt_dict) -> pd.DataFrame`

**目的**：驗證「5 張圖通用」加分項，固定參數不手調即可正確計數。

**Ground Truth 來源**：BCCD Dataset 附帶的 XML annotation（`Annotations/*.xml`），解析出每張圖的 RBC/WBC/Platelet 真實數量。

**輸出欄位**
| image | rbc_pred | rbc_gt | rbc_err% | wbc_pred | wbc_gt | wbc_err% | platelet_pred | platelet_gt | platelet_err% |
|-------|----------|--------|----------|----------|--------|----------|---------------|-------------|---------------|

**誤差計算**：`err% = abs(pred - gt) / gt × 100`

---

## 十、Streamlit App（§8）

### UI 配置

```
Sidebar
├── 影像來源：上傳 / 5 張範例切換（radio）
├── 參數滑桿
│   ├── Gaussian Kernel Size  (3–11，步進 2，預設 5)
│   ├── Adaptive Block Size   (11–101，步進 2，預設 51)
│   ├── Adaptive C            (1–15，預設 5)
│   ├── Morph Kernel Size     (1–9，步進 2，預設 3)
│   └── Min Cell Area         (20–200，預設 50)
└── Reset 按鈕（恢復預設值）

Main Area
├── Tab 1「Pipeline 可視化」
│   └── 6 格網格：原圖 / 灰階 / 模糊 / 二值化 / 形態學 / 輪廓疊加
├── Tab 2「分類結果」
│   ├── 標註圖（三類不同顏色）
│   └── 計數表：RBC / WBC / Platelet 預測數量
└── Tab 3「Watershed」
    └── 切分前 vs 切分後並排對比

底部（任何 Tab 均顯示）
└── st.download_button：「下載標註圖 PNG」
```

### 啟動方式（Colab）

```python
%%writefile app.py
# ... streamlit code ...

from pyngrok import ngrok
import subprocess

proc = subprocess.Popen(["streamlit", "run", "app.py", "--server.port=8501"])
public_url = ngrok.connect(8501)
print(f"Streamlit URL: {public_url}")
```

---

## 十一、繳交產物

| 產物 | 說明 |
|------|------|
| `Final_Project.ipynb` | Colab 連結，所有 cell 已執行並有輸出 |
| `report.pdf` | Pipeline 架構圖、演算法說明、實驗結果表、困難案例分析 |

---

## 十二、分數對應檢查清單

| 評分項目 | 對應 Notebook 區塊 | 目標分 |
|----------|-------------------|-------|
| 影像前處理 Pipeline 可視化 | §2 + §8 Tab 1 | 15 分 |
| WBC 計數（±30%） | §3 + §6 | 25 分 |
| Streamlit UI（切換/參數/下載） | §8 | 10 分 |
| 程式碼品質（結構 + 中文註解） | 全區塊 | 10 分 |
| 三種細胞分類（±30%） | §4 | +15 分 |
| Watershed 重疊切分 | §5 | +15 分 |
| 5 張圖通用（固定參數） | §7 | +5 分 |
| 書面報告 PDF | report.pdf | +10 分 |
| **合計** | | **105 分** |
