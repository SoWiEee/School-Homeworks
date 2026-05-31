# HPCxAI_Camp_2025

這個資料夾整理了 HPCxAI camp 的練習與競賽程式，主題涵蓋 **CUDA、OpenACC、MPI、LLM fine-tuning、科學計算**。

## 目錄總覽

- `lab_cuda/`：CUDA 基礎 Lab（CPU/GPU 矩陣乘法）
- `lab_acc/`：OpenACC Lab（簡易 NN 推論，MNIST）
- `comp_cuda/`：CUDA 競賽題（Sobel 邊緣偵測，含共享記憶體優化）
- `comp_mpi/`：MPI 競賽題（Mandelbrot 平行化）
- `comp_BERT_Finetune/`：BERT 訓練與推論腳本
- `comp_specfem3d/`：SPECFEM3D 地震波模擬相關檔案與編譯結果

## 各子專案簡介

### 1) `lab_cuda`

- `matrix_mul_cpu.cc`：CPU 版本矩陣乘法
- `matrix_mul_gpu.cu`：GPU 版本矩陣乘法（kernel + grid/block 設定）
- `Makefile`：編譯腳本

重點：比較 CPU 與 GPU 計算時間，理解 global memory access 與 thread block 配置。

### 2) `lab_acc`

- `nn.cpp`：兩層全連接神經網路推論（MNIST）
- `#pragma acc` 用於平行化 `LinearLayer`、`Sigmoid`、`Argmax`

重點：學習 OpenACC 指令式加速、資料搬移（copyin/copyout）與效能觀察。

### 3) `comp_cuda`

- `sobel.cu`：PNG 影像 Sobel 濾波
- 使用 `__constant__` 存 mask、`__shared__` tile 降低 global memory 存取成本

重點：2D stencil 類型問題在 CUDA 的 shared memory 優化手法。

### 4) `comp_mpi`

- `mandelbrot_parallel.cpp`：Mandelbrot 集合平行計算

重點：工作切分與多程序計算結果整合。

### 5) `comp_BERT_Finetune`

- `Train.py` / `run_train.sh`：BERT 訓練流程
- `Inference.py` / `run_inf.sh`：推論流程
- `bert-*.out/.err`：執行紀錄

重點：NLP 模型在 HPC 環境中的訓練/推論腳本化。

## 建議環境

- Linux
- NVIDIA GPU + CUDA Toolkit（CUDA/OpenACC 相關子專案）
- MPI runtime（MPI 子專案）
- Python + Transformers 生態套件（BERT 子專案）

## 備註

這個資料夾偏向「課程實作與競賽練習紀錄」，不同子專案的建置方式獨立（請優先查看各子資料夾內的 `Makefile`、`.sh`、或既有 README）。
