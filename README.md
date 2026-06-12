# School-Homeworks

這個 repository 是學校作業、課程練習與期末專案的總整理。根目錄提供快速導航；每個子資料夾則各自保存完整程式碼、測資、實驗紀錄、報告或專案 README。

本 repo 不是單一應用程式，而是多個彼此獨立的課程專案集合。不同資料夾使用的語言、依賴與建置流程都不同，重現結果時請以各子專案內的 README、Makefile、Dockerfile、notebook 或腳本為準。

## 專案導航

| 專案 | 主題 | 主要技術 | 時間 | 連結 |
|---|---|---|---|---|
| C++ 練習 | 基礎程式設計、作業、考古題 | C++ | 2024-02 ~ 2024-06 | [CPP/](CPP/) |
| Java 課堂範例 | 物件導向、繼承、介面、測驗題 | Java | 2024-09 ~ 2025-01 | [Java-Course-Example/](Java-Course-Example/) |
| Rest | 餐廳座位與資源配置模擬 | C++、CSV 測資 | 2025-12 ~ 2026-01 | [Rest/](Rest/) |
| HPCxAI Camp 2025 | CUDA、OpenACC、MPI、BERT、科學計算 | CUDA、OpenACC、MPI、Python | 2025-07 | [HPCxAI_Camp_2025/](HPCxAI_Camp_2025/) |
| Speech Emotion Recognition | MFCC + 1D CNN 語音情緒辨識 | Python、Librosa、TensorFlow/Keras | 2025-09 ~ 2026-01 | [Speech-Emotion-Recognition/](Speech-Emotion-Recognition/) |
| Creditcard Transaction | 信用卡交易流程模擬：授權、結算、作廢、退款 | Vue 3、Go Chi、PostgreSQL、Redis、Docker | 2025-09 ~ 2026-01 | [Creditcard-Transaction/](Creditcard-Transaction/) |
| 3D Gasket | Sierpinski Tetrahedron 分形渲染 | C++17、OpenGL 4.5、GLFW、GLM、ImGui | 2025-09 ~ 2025-11 | [3D-Gasket/](3D-Gasket/) |
| Cyberpunk Renderer | OpenGL 延遲渲染與城市夜景特效 | C++、OpenGL 4.5、Deferred Shading、SSAO、Bloom | 2025-09 ~ 2026-01 | [Cyberpunk-Renderer/](Cyberpunk-Renderer/) |
| Image Enhancement | 影像診斷、增強方法比較與失敗案例分析 | MATLAB | 2026-02 ~ 2026-04 | [Image-Enhancement/](Image-Enhancement/) |
| Recon Blood | 血液抹片細胞自動辨識與計數 | Python、OpenCV、Streamlit、scikit-image | 2026-06 | [Recon-Blood/](Recon-Blood/) |

## 專案簡介

### C++ 練習

[CPP/](CPP/) 收錄 C++ 課程期間的平時作業、日期分類練習與歷屆考古題解答。內容以基礎語法、流程控制、函式、類別、資料結構基礎與解題能力訓練為主。

常見執行方式：

```bash
g++ -std=c++17 -O2 -o run Q1.cpp
./run
```

### Java 課堂範例

[Java-Course-Example/](Java-Course-Example/) 收錄 Java 課堂練習與測驗題，內容涵蓋類別設計、封裝、繼承、多型、介面、例外處理與簡單應用題。資料夾多以日期或測驗題號分類。

### Rest

[Rest/](Rest/) 是餐廳座位與資源配置相關的 C++ 模擬作業，包含開發測資與正式測資。測資涵蓋基本排程、deadlock、race condition、資源耗盡與複雜案例。初始資源設定包含單人座、四人沙發、六人沙發、嬰兒椅與輪椅。

主要檔案：

- `main.cpp`：主要解法。
- `main_bypass.cpp`、`sushi_safe.cpp`：其他版本或實驗解法。
- `test_*.csv`：正式測資。
- `base.csv`、`deadlock.csv`、`race.csv`、`preoccupied.csv`：開發測資。

### HPCxAI Camp 2025

[HPCxAI_Camp_2025/](HPCxAI_Camp_2025/) 整理 HPCxAI camp 的 lab 與競賽程式：

- `lab_cuda/`：CPU/GPU 矩陣乘法。
- `lab_acc/`：OpenACC 平行化簡易 NN 推論。
- `lab_mpi/`：MPI 基礎通訊與平行計算。
- `comp_cuda/`：CUDA Sobel 邊緣偵測與 shared memory 優化。
- `comp_mpi/`：Mandelbrot 平行化。
- `comp_BERT_Finetune/`：BERT 訓練與推論腳本。
- `comp_specfem3d/`：SPECFEM3D 地震波模擬相關檔案。

### Speech Emotion Recognition

[Speech-Emotion-Recognition/](Speech-Emotion-Recognition/) 實作語音情緒辨識實驗，使用 MFCC 特徵搭配 1D CNN 分類語音情緒。流程包含音訊載入、固定長度裁切、noise/pitch augmentation、MFCC 擷取、模型訓練與 confusion matrix / classification report 評估。

主要入口：

- `SER.ipynb`：主要 notebook。
- `README.md`：論文方法、模型架構與實作設定說明。

### Creditcard Transaction

[Creditcard-Transaction/](Creditcard-Transaction/) 是資料庫系統全端專案，用來模擬信用卡核心交易流程：

- 授權 / 消費 (`pay`)
- 延遲結算 (`settlement`)
- 作廢 (`void`)
- 退款 (`refund`)
- 點數回饋與點數折抵
- 信用額度檢查與基本風控

架構：

- `frontend/`：Vue 3 + Vite 單頁應用。
- `backend_go/`：Go Chi REST API。
- `db/init.sql`：PostgreSQL schema 初始化。
- `redis`：輔助快取或風控狀態。
- `nginx/`：反向代理設定。
- `loadtest/`：JMeter / k6 壓測腳本。

開發啟動：

```bash
cd Creditcard-Transaction
docker compose up --build
```

預設服務：

- Frontend: <http://localhost:5173>
- Backend: <http://localhost:3000>
- PostgreSQL: `localhost:5432`

### 3D Gasket

[3D-Gasket/](3D-Gasket/) 是 C++ / OpenGL 4.5 的 3D 分形渲染專案，實作 Sierpinski Tetrahedron 的 volume subdivision。程式使用現代 OpenGL pipeline、GLFW、GLM 與 Dear ImGui，並提供右鍵選單調整 subdivision level。

建置方式：

```bash
cd 3D-Gasket
mkdir build
cd build
cmake ..
cmake --build .
```

### Cyberpunk Renderer

[Cyberpunk-Renderer/](Cyberpunk-Renderer/) 是 C++ / OpenGL 4.5 即時渲染專案，以 deferred shading 為核心，加入 G-buffer、SSAO、Bloom、Skybox、大量動態點光源與 instanced mesh，呈現 cyberpunk 風格城市夜景。

主要入口：

- `main.cpp`：場景建立與 render loop。
- `core/`：Camera、Shader、GBuffer 與渲染模組。
- `assets/shaders/`：GLSL shader。
- `Cyberpunk-Renderer.sln`：Windows / Visual Studio 專案檔。

### Image Enhancement

[Image-Enhancement/](Image-Enhancement/) 是影像處理期中專案，使用 MATLAB 完成影像診斷、增強方法比較與失敗案例分析。內容包含亮度、對比度、色偏診斷，並比較 Gamma correction、Global Histogram Equalization、CLAHE、RGB / YCbCr 色彩校正等方法。

主要檔案：

- `task_a.m`：影像統計與診斷。
- `task_b.m`：增強方法比較。
- `task_c.m`：失敗案例分析與改善。
- `output/`：實驗輸出圖。
- `ai_log.md`：AI 協作紀錄。

### Recon Blood

[Recon-Blood/](Recon-Blood/) 是影像處理期末專案，目標是用傳統影像處理方法自動偵測與計數血液抹片中的 WBC、RBC 與 Platelet。專案明確不使用深度學習，而是使用 OpenCV / scikit-image 的可解釋規則 pipeline。

核心功能：

- Streamlit 互動式 App。
- 灰階、Gaussian Blur、Adaptive Thresholding、Morphological Closing 等前處理視覺化。
- WBC / RBC / Platelet 三類細胞偵測與計數。
- RBC Hough circle 補強與 Watershed + Distance Transform 視覺化。
- YOLO 格式標註讀取與 IoU 評估。
- 預測疊圖、預測框 CSV、計數誤差 CSV 下載。

主要檔案：

- `app.py`：Streamlit App。
- `blood_cell_detector.py`：核心偵測器與影像處理工具。
- `eval_iou.py`：批次 IoU 評估腳本。
- `report.md`：設計決策、修正歷程與結果分析。
- `TXL_PBC_Streamlit_Colab.ipynb`：Colab demo notebook。

本機啟動：

```bash
cd Recon-Blood
pip install -r requirements.txt
streamlit run app.py
```

## 使用方式

1. 先從「專案導航」選擇要查看的子資料夾。
2. 優先閱讀該子專案的 `README.md`。
3. 若是 C++ / CUDA / MPI 專案，查看 `Makefile`、`.sln`、`.vcxproj` 或 `CMakeLists.txt`。
4. 若是 Python 專案，查看 `requirements.txt`、notebook 或 `*.py` 入口。
5. 若是全端專案，優先查看 `docker-compose.yml`、`Dockerfile` 與前後端 README。

## Repository 備註

- 本 repo 以課程學習紀錄為主，部分資料夾包含實驗檔、測資、輸出圖或報告草稿。
- 大型資料集、第三方 vendor code 或編譯產物可能只為了重現課程成果而保留。
- 不同子專案的 dependency 彼此獨立，沒有統一的根目錄安裝流程。
- 若要重現結果，請依各子專案 README 內的版本、環境與執行方式操作。
