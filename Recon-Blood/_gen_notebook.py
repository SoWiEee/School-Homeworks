"""Generate the self-contained Colab notebook used for the final demo.

The notebook writes the project source via %%writefile cells, installs only the
runtime dependencies, clones the dataset, runs the all-dataset evaluation, and
launches the Streamlit app.
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
NB_PATH = HERE / "TXL_PBC_Streamlit_Colab.ipynb"

detector_src = (HERE / "blood_cell_detector.py").read_text(encoding="utf-8")
app_src = (HERE / "app.py").read_text(encoding="utf-8")
eval_src = (HERE / "eval_iou.py").read_text(encoding="utf-8")

def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text}


def code(text):
    return {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": text,
    }


cells = []

cells.append(md(
    "# TXL-PBC 傳統影像處理血球計數器 — 可獨立執行的 Colab Notebook\n"
    "\n"
    "這份 Notebook 完全自給自足，由上而下依序執行每個 cell 就會：\n"
    "\n"
    "1. 透過 `%%writefile` 把專案原始碼（`blood_cell_detector.py`、`app.py`、`eval_iou.py`）寫到磁碟。\n"
    "2. 安裝所需的相依套件。\n"
    "3. 從 GitHub 下載（clone）TXL-PBC 資料集。\n"
    "4. 對整個資料集跑 **IoU 評估**，印出各類別與 micro 的 P / R / F1 與計數誤差。\n"
    "5. 透過暫時性的 Cloudflare tunnel 啟動 Streamlit 互動式 App。\n"
    "\n"
    "不需要上傳專案、也不需要任何模型檔。偵測完全是**規則式（rule-based）**的，"
    "只用 OpenCV / NumPy / scikit-image 這類傳統影像處理工具。\n"
    "\n"
    "---\n"
    "\n"
    "### 演算法總覽\n"
    "\n"
    "整體流程是「**先抓白血球，再排除、最後分紅血球與血小板**」。白血球的細胞核是最明顯的"
    "紫羅蘭色區塊，先把它框出來，後面就不會把同一顆白血球誤算成紅血球或血小板。\n"
    "\n"
    "| 細胞 | 主要判斷依據 | 為什麼這樣設計 |\n"
    "| --- | --- | --- |\n"
    "| **WBC 白血球** | 紫羅蘭色細胞核 + 深染檢查 | 白血球核顏色最特別，先抓出來也能避免後面重複計數 |\n"
    "| **RBC 紅血球** | 自適應二值化輪廓 + 面積/圓度/尺寸規則 + Hough 圓 | 紅血球大小穩定、接近圓形，用幾何比用顏色可靠 |\n"
    "| **Platelet 血小板** | 小型紫色元件 + 顆粒紋理 + 圓形度 | 血小板很小，必須用紋理和形狀排除紫色雜點 |\n"
    "\n"
    "所有尺寸門檻都掛在 `shape_rbc_radius()` 算出的紅血球半徑 `r0` 上（純粹由影像解析度推得，"
    "不使用任何標註資訊），因此同一套規則能適應資料集中不同尺寸的影像。\n"
    "\n"
    "評估採用助教指定的 **IoU 比對**：YOLO 標註先轉成像素框，預測框必須同類別且和 GT 有足夠重疊，"
    "才算偵測成功。"
))

cells.append(md(
    "## 1. 寫出偵測模組 `blood_cell_detector.py`\n"
    "\n"
    "`%%writefile` 會把這個 cell 的內容傾印成 `blood_cell_detector.py`，讓後面的 App 可以 import。\n"
    "\n"
    "這個模組包含整套演算法，下面是幾個主要函式的白話說明：\n"
    "\n"
    "- **`shape_rbc_radius(h, w)`**：依影像解析度回傳紅血球半徑 `r0`，是所有尺寸門檻的尺度基準。\n"
    "- **`wbc_violet_mask(img)`**：找白血球核常見的紫羅蘭色區域。\n"
    "- **`detect_wbc(img)`**：先抓白血球，保留像細胞核的大型深紫區，排除小紫點與染色暈染。\n"
    "- **`detect_rbc_rule(...)`**：用二值化後的輪廓找紅血球，再用面積、圓度、長寬比和 `r0` 篩選。\n"
    "- **`hough_rbc_candidates(...)`**：補回輪廓不完整或彼此相連的紅血球。\n"
    "- **`detect_platelets_rule(...)`**：找小型紫色元件，再用顆粒紋理、顏色深度和圓形度判斷是不是血小板。\n"
    "- **`watershed_*`**：用 Distance Transform + Watershed 顯示紅血球重疊區怎麼被切開，預設只作視覺化。"
))
cells.append(code("%%writefile blood_cell_detector.py\n" + detector_src))

cells.append(md(
    "## 2. 寫出 Streamlit App `app.py`\n"
    "\n"
    "`%%writefile` 會把這個 cell 的內容傾印成 `app.py`。這支 App 提供互動式介面：選擇影像、"
    "顯示前處理各階段、疊上預測框、列出三種細胞的計數與誤差，並可下載 PNG / CSV 結果。"
))
cells.append(code("%%writefile app.py\n" + app_src))

cells.append(md(
    "## 3. 寫出評估腳本 `eval_iou.py`\n"
    "\n"
    "`%%writefile` 會把這個 cell 傾印成 `eval_iou.py`，供第 6 節的「全資料集評估」使用，"
    "也可在終端機直接執行 `python eval_iou.py --split test --iou 0.3`。\n"
    "\n"
    "評估方式完全依助教規格：YOLO 標註轉像素框（含邊界裁切）→ 與預測框同類別、"
    "**一對一貪婪比對**（IoU 由高到低配對）→ 統計各類別與 micro 的 Precision / Recall / F1。"
))
cells.append(code("%%writefile eval_iou.py\n" + eval_src))

cells.append(md(
    "## 4. 安裝相依套件\n"
    "\n"
    "只安裝執行 App 與傳統影像處理需要的套件；偵測流程不需要模型檔。"
))
cells.append(code(
    "import subprocess, sys\n"
    "\n"
    "# OpenCV / NumPy 是主要偵測工具；scikit-image 用於 Watershed 視覺化。\n"
    "pkgs = [\n"
    "    'streamlit>=1.32',\n"
    "    'opencv-python-headless>=4.8',\n"
    "    'numpy>=1.24',\n"
    "    'pandas>=2.0',\n"
    "    'scikit-image>=0.21',  # 用於分水嶺 (watershed) 視覺化\n"
    "    'pillow>=10.0',\n"
    "    'matplotlib>=3.7',\n"
    "]\n"
    "subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', *pkgs])\n"
    "print('相依套件安裝完成。')"
))

cells.append(md(
    "## 5. 取得 TXL-PBC 資料集（git clone）\n"
    "\n"
    "App 可以用內建的範例樣本執行，但 Demo 建議使用完整資料集，這樣才能切換 "
    "train / val / test。這裡直接從 GitHub 做淺層 clone（`--depth 1`），repo 已把影像與標註"
    "放在 `TXL-PBC/` 底下，不需要解壓縮。若資料集已存在則直接重用。"
))
cells.append(code(
    "import os, subprocess\n"
    "\n"
    "DATASET_REPO = 'https://github.com/lugan113/TXL-PBC_Dataset.git'\n"
    "\n"
    "# Colab 與本機路徑可能不同，逐一嘗試。\n"
    "CANDIDATE_ROOTS = [\n"
    "    'TXL-PBC_Dataset/TXL-PBC',\n"
    "    './TXL-PBC_Dataset/TXL-PBC',\n"
    "    '/content/TXL-PBC_Dataset/TXL-PBC',\n"
    "]\n"
    "\n"
    "def find_dataset():\n"
    "    # 同時有 images/ 與 labels/ 子資料夾才算是有效的資料集根目錄。\n"
    "    for root in CANDIDATE_ROOTS:\n"
    "        if os.path.exists(os.path.join(root, 'images')) and os.path.exists(os.path.join(root, 'labels')):\n"
    "            return root\n"
    "    return None\n"
    "\n"
    "root = find_dataset()\n"
    "if root is None:\n"
    "    print('正在 clone TXL-PBC 資料集（淺層）...')\n"
    "    subprocess.check_call(['git', 'clone', '--depth', '1', DATASET_REPO, 'TXL-PBC_Dataset'])\n"
    "    root = find_dataset()\n"
    "\n"
    "print('資料集根目錄:', root if root else '找不到；App 將改用內建範例樣本')"
))

cells.append(md(
    "## 6. 全資料集評估（All Eval）\n"
    "\n"
    "對**整個資料集**（train + val + test，共 1260 張）逐張跑完整偵測，依助教的 IoU 規格"
    "統計各類別與 micro 的 Precision / Recall / F1（同時列出 **IoU 0.3** 與較嚴格的 **IoU 0.5**），"
    "並附三種細胞的**計數誤差**（±30% 為基本要求）。這樣助教可以直接在這裡看到完整指標。\n"
    "\n"
    "> ⚠️ 全資料集評估需逐張偵測（含 Hough 圓偵測），在 Colab CPU 上約需數分鐘；"
    "下方會每 100 張印一次進度。若只想快速看單一 split，可把 `splits` 改成 `['test']`。"
))
cells.append(code(
    "import os, glob\n"
    "from blood_cell_detector import detect_cells, load_image, CLASS_NAMES\n"
    "from eval_iou import load_yolo_gt_clipped, match_one_to_one\n"
    "import pandas as pd\n"
    "try:\n"
    "    from IPython.display import display\n"
    "except ImportError:\n"
    "    display = print\n"
    "\n"
    "# 找出可用的資料集根目錄。\n"
    "root = None\n"
    "for candidate in ['TXL-PBC_Dataset/TXL-PBC', '/content/TXL-PBC_Dataset/TXL-PBC', './TXL-PBC_Dataset/TXL-PBC']:\n"
    "    if os.path.exists(os.path.join(candidate, 'images')) and os.path.exists(os.path.join(candidate, 'labels')):\n"
    "        root = candidate\n"
    "        break\n"
    "print('資料集根目錄:', root)\n"
    "\n"
    "splits = ['train', 'val', 'test']   # 本報告使用整個資料集；想快速測試可改成 ['test']\n"
    "thrs = [0.3, 0.5]\n"
    "tot = {t: {c: [0, 0, 0] for c in (0, 1, 2)} for t in thrs}   # t -> class -> [tp, fp, fn]\n"
    "gt_count = {c: 0 for c in (0, 1, 2)}\n"
    "pred_count = {c: 0 for c in (0, 1, 2)}\n"
    "\n"
    "paths = [p for s in splits for p in sorted(glob.glob(os.path.join(root, 'images', s, '*.png')))]\n"
    "print(f'評估影像數: {len(paths)}（{\"+\".join(splits)}）。逐張偵測中，約需數分鐘…')\n"
    "for i, p in enumerate(paths, 1):\n"
    "    img = load_image(p)\n"
    "    h, w = img.shape[:2]\n"
    "    gts = load_yolo_gt_clipped(p, root, w, h)\n"
    "    preds = detect_cells(img)   # 預設流程：WBC 先行、RBC 輪廓 + Hough、血小板規則偵測\n"
    "    for c in (0, 1, 2):\n"
    "        ps = [b for b in preds if int(b[0]) == c]\n"
    "        gs = [g for g in gts if int(g[0]) == c]\n"
    "        pred_count[c] += len(ps)\n"
    "        gt_count[c] += len(gs)\n"
    "        for t in thrs:   # 同一次偵測，於兩個 IoU 門檻各自比對\n"
    "            tp, fp, fn = match_one_to_one(ps, gs, t)\n"
    "            tot[t][c][0] += tp; tot[t][c][1] += fp; tot[t][c][2] += fn\n"
    "    if i % 100 == 0 or i == len(paths):\n"
    "        print(f'  進度 {i}/{len(paths)}')\n"
    "\n"
    "def make_df(t):\n"
    "    rows = []\n"
    "    micro = [0, 0, 0]\n"
    "    for c in (0, 1, 2):\n"
    "        tp, fp, fn = tot[t][c]\n"
    "        micro[0] += tp; micro[1] += fp; micro[2] += fn\n"
    "        P = tp / (tp + fp) if tp + fp else 0.0\n"
    "        R = tp / (tp + fn) if tp + fn else 0.0\n"
    "        F = 2 * P * R / (P + R) if P + R else 0.0\n"
    "        rows.append({'class': CLASS_NAMES[c], 'TP': tp, 'FP': fp, 'FN': fn,\n"
    "                     'Precision': round(P, 3), 'Recall': round(R, 3), 'F1': round(F, 3)})\n"
    "    tp, fp, fn = micro\n"
    "    P = tp / (tp + fp) if tp + fp else 0.0\n"
    "    R = tp / (tp + fn) if tp + fn else 0.0\n"
    "    F = 2 * P * R / (P + R) if P + R else 0.0\n"
    "    rows.append({'class': 'micro', 'TP': tp, 'FP': fp, 'FN': fn,\n"
    "                 'Precision': round(P, 3), 'Recall': round(R, 3), 'F1': round(F, 3)})\n"
    "    return pd.DataFrame(rows).set_index('class')\n"
    "\n"
    "for t in thrs:\n"
    "    print(f'\\n=== IoU {t} ===')\n"
    "    display(make_df(t))\n"
    "\n"
    "print('\\n=== 計數誤差（±30% 為基本要求）===')\n"
    "count_rows = []\n"
    "for c in (0, 1, 2):\n"
    "    g, pr = gt_count[c], pred_count[c]\n"
    "    err = (pr - g) / g * 100 if g else 0.0\n"
    "    ok = '✅' if abs(err) <= 30 else '❌'\n"
    "    count_rows.append({'class': CLASS_NAMES[c], 'GT': g, 'Pred': pr,\n"
    "                       '誤差 %': f'{err:+.1f}%', '±30%': ok})\n"
    "display(pd.DataFrame(count_rows).set_index('class'))"
))

cells.append(md(
    "## 7. 以 cloudflared 啟動 Streamlit\n"
    "\n"
    "執行這個 cell 後，開啟印出來的公開網址即可使用 App。使用期間請保持這份 Notebook 持續執行。"
))
cells.append(code(
    "import subprocess, time, re, os\n"
    "\n"
    "CF_URL = 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64'\n"
    "CF_BIN = './cloudflared'\n"
    "\n"
    "# 若重複執行此 cell，先關掉舊的 App / tunnel 程序，避免佔用埠號。\n"
    "for name in ['streamlit_proc', 'cf_proc']:\n"
    "    proc = globals().get(name)\n"
    "    if proc is not None and proc.poll() is None:\n"
    "        proc.terminate()\n"
    "        time.sleep(1)\n"
    "\n"
    "# 下載 cloudflared；wget 失敗就改用 curl。\n"
    "if not os.path.exists(CF_BIN):\n"
    "    print('正在下載 cloudflared...')\n"
    "    ok = subprocess.run(['wget', '-q', CF_URL, '-O', CF_BIN]).returncode == 0\n"
    "    if not ok:\n"
    "        ok = subprocess.run(['curl', '-sL', CF_URL, '-o', CF_BIN]).returncode == 0\n"
    "    if not ok:\n"
    "        raise RuntimeError('cloudflared 下載失敗，請檢查網路設定或改用 Colab 的埠轉發。')\n"
    "    subprocess.run(['chmod', '+x', CF_BIN])\n"
    "    print('cloudflared 下載完成。')\n"
    "\n"
    "# 在背景啟動 Streamlit。\n"
    "streamlit_proc = subprocess.Popen(\n"
    "    ['streamlit', 'run', 'app.py',\n"
    "     '--server.port=8501',\n"
    "     '--server.headless=true',\n"
    "     '--server.enableCORS=false',\n"
    "     '--server.enableXsrfProtection=false'],\n"
    "    stdout=subprocess.DEVNULL,\n"
    "    stderr=subprocess.DEVNULL\n"
    ")\n"
    "time.sleep(3)\n"
    "\n"
    "# 啟動 Cloudflare tunnel，並從 stderr 解析出公開網址。\n"
    "cf_proc = subprocess.Popen(\n"
    "    [CF_BIN, 'tunnel', '--url', 'http://localhost:8501'],\n"
    "    stdout=subprocess.DEVNULL,\n"
    "    stderr=subprocess.PIPE\n"
    ")\n"
    "\n"
    "url = None\n"
    "for line in cf_proc.stderr:\n"
    "    text = line.decode('utf-8', errors='ignore')\n"
    "    match = re.search(r'https://[a-z0-9\\-]+\\.trycloudflare\\.com', text)\n"
    "    if match:\n"
    "        url = match.group(0)\n"
    "        break\n"
    "\n"
    "print('Streamlit App 已啟動。')\n"
    "print(f'公開網址: {url}')\n"
    "print('開啟上面的網址即可使用互動式 App。')"
))

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
        "colab": {"provenance": []},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

NB_PATH.write_text(json.dumps(notebook, indent=1, ensure_ascii=False), encoding="utf-8")
print("Wrote", NB_PATH)
print("Cells:", len(cells))
