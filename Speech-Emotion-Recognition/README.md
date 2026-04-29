# Speech-Emotion-Recognition with 1D CNN and MFCC

本專案實作一個 Speech Emotion Recognition, SER 系統，使用 **MFCC 特徵**搭配 **1D CNN** 進行情緒分類。  
專案核心參考論文為 **Speech Emotion Recognition Based on 1D CNN and MFCC**，並以 Python、Librosa、TensorFlow/Keras 完成資料前處理、特徵擷取、模型訓練與評估。

## 專案目標

語音情緒辨識的目的是從語音訊號中推測說話者的情緒狀態，例如 happy、sad、angry、fearful 等。  
本專案希望透過經典且可解釋的流程，建立一個可重現的 SER 實驗：

1. 讀取語音資料集  
2. 進行固定長度切分與資料增強  
3. 擷取 MFCC 特徵  
4. 使用 1D CNN 進行情緒分類  
5. 以 accuracy、confusion matrix、classification report 進行評估  

## 參考論文

[Gaoyun Li, Yong Liu, Xiong Wang, Speech Emotion Recognition Based on 1D CNN and MFCC](https://ieeexplore.ieee.org/document/10351697)

論文提出的核心方法包含：

- 將語音樣本統一成固定長度 **2.5 秒**
- 使用 **adding noise** 與 **pitch shifting** 做資料增強
- 以 **20 維 MFCC** 作為輸入特徵
- 使用 **5 個 convolution blocks** 的 **1D CNN**
- 在 **CREMA-D** 與 **RAVDESS** 資料集上進行實驗

論文中報告的結果為：

- **CREMA-D**: 94.69%
- **RAVDESS**: 97.33%

以上內容來自參考論文的方法與實驗章節。

## 本專案實作內容

### 1. 資料集準備

目前程式包含兩組資料來源：

- **RAVDESS**
  - 程式中可自動下載並解壓縮
- **CREMA-D**
  - 程式註解指出需要自行準備 `CREMA-D.zip`

程式會將資料解壓到：

- `./ravdess_data`
- `./crema_data`

### 2. 前處理與資料增強

本專案對音訊做以下處理：

- 使用 `librosa.load(..., duration=2.5, offset=0.5, sr=22050)` 載入音訊
- 若長度不足則補零，過長則截斷，統一成 **2.5 秒**
- 進行兩種 augmentation：
  - 加噪聲 `noise`
  - 音高平移 `pitch`

這部分和論文的方法設計一致。

### 3. 特徵擷取

本專案使用 **MFCC** 作為輸入特徵，設定如下：

- `sr = 22050`
- `n_mfcc = 20`
- `n_fft = 2048`
- `hop_length = 512`

擷取後將 MFCC 轉成 `(time, features)` 格式，並固定為 **108 frames**，方便輸入神經網路。  
此設計對應論文中對 MFCC 的描述。

### 4. 模型架構

模型為一個 1D CNN，主要結構如下：

- 5 個 Conv1D blocks
- 每個 block 包含：
  - Conv1D
  - BatchNormalization
  - ReLU
  - MaxPooling1D
  - Dropout
- 最後接：
  - Flatten
  - Dense(512)
  - Dropout
  - BatchNormalization
  - ReLU
  - Softmax output

各層卷積設定為：

- 512 filters, kernel size 5
- 512 filters, kernel size 5
- 256 filters, kernel size 5
- 256 filters, kernel size 3
- 128 filters, kernel size 3

這與論文中的 1D CNN 架構基本一致。

### 5. 訓練設定

目前程式中的訓練設定：

- Optimizer: `AdamW`
- Learning rate: `0.0001`
- Weight decay: `5e-4`
- Batch size: `64`
- Epochs: `50`
- Loss: `categorical_crossentropy`

其中 batch size 與 epochs 和論文一致，但 learning rate 與論文文中提到的 `0.001` 不同，因此本專案屬於「參考論文後的實作版本」，不是完全逐字重現。

### 6. 評估方式

本專案輸出以下評估結果：

- Training / validation accuracy curve
- Training / validation loss curve
- Test accuracy
- Confusion matrix
- Classification report

這與論文中的實驗分析方向一致。

---

## 專案結構

```bash
.
├── ser.py
├── CREMA-D.zip                  # 需自行準備
├── ravdess_data.zip             # 程式可自動下載
├── ravdess_data/                # 解壓後資料夾
├── crema_data/                  # 解壓後資料夾
└── README.md
```

## 安裝需求

- 建議使用 `Python 3.10+`。
- 套件安裝
```bash
pip install resampy librosa==0.10.1 matplotlib seaborn scikit-learn tensorflow pandas
```
