"""Generate a self-contained Colab notebook that writes the project source via
%%writefile cells, downloads the trained model, clones the dataset, and launches
the Streamlit App. Run once, then delete this script."""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
NB_PATH = HERE / "TXL_PBC_Streamlit_Colab.ipynb"

detector_src = (HERE / "blood_cell_detector.py").read_text(encoding="utf-8")
app_src = (HERE / "app.py").read_text(encoding="utf-8")

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
    "1. 透過 `%%writefile` 把專案原始碼（`blood_cell_detector.py`、`app.py`）寫到磁碟。\n"
    "2. 安裝所需的相依套件。\n"
    "3. 從 GitHub 下載（clone）TXL-PBC 資料集。\n"
    "4. 透過暫時性的 Cloudflare tunnel 啟動 Streamlit 互動式 App。\n"
    "\n"
    "不需要上傳專案、也不需要任何模型檔。偵測完全是**規則式（rule-based）**的，"
    "只用傳統影像處理，沒有深度學習、也沒有訓練好的模型。\n"
    "\n"
    "---\n"
    "\n"
    "### 演算法總覽\n"
    "\n"
    "整體流程是「**先抓白血球，再排除、最後分紅血球與血小板**」，核心理由是：白血球的細胞核"
    "染成紫羅蘭色、面積最大也最好辨識，先把它框出來，就能避免它被誤切成好幾顆紅血球或血小板。\n"
    "\n"
    "| 細胞 | 主要判斷依據 | 為什麼這樣設計 |\n"
    "| --- | --- | --- |\n"
    "| **WBC 白血球** | 紫羅蘭色相 (HSV H∈[120,158]) + 形態學開運算取核心 | 細胞核染色最深、色相最純，用「窄色相 + 寬飽和度」連淡染的核也抓得到，又不會把成團的紅血球（偏粉紅）誤判 |\n"
    "| **RBC 紅血球** | 自適應二值化輪廓 + 面積/圓度/尺寸規則 | 數量多、大小一致；用由解析度推得的半徑 `r0` 當尺度基準，門檻不偷看標註 |\n"
    "| **Platelet 血小板** | 小型紫色團塊 + 顆粒紋理 (S 標準差、灰階標準差) | 真血小板內部有顆粒紋理，用「變異度」把它和均勻的紫色雜訊區分開 |\n"
    "\n"
    "所有尺寸門檻都掛在 `shape_rbc_radius()` 算出的紅血球半徑 `r0` 上（純粹由影像解析度推得，"
    "不使用任何標註資訊），因此同一套規則能適應資料集中不同尺寸的影像。\n"
    "\n"
    "評估採用助教指定的 **IoU 比對**：把 YOLO 標註轉成像素框，與預測框做一對一貪婪比對，"
    "同類別且 IoU 超過門檻才算 TP，藉此在視覺上確認「框到差不多正確的位置」。"
))

cells.append(md(
    "## 1. 寫出偵測模組 `blood_cell_detector.py`\n"
    "\n"
    "`%%writefile` 會把這個 cell 的內容傾印成 `blood_cell_detector.py`，讓後面的 App 可以 import。\n"
    "\n"
    "這個模組包含整套演算法，重點函式與其演算法意涵：\n"
    "\n"
    "- **`shape_rbc_radius(h, w)`**：依影像解析度回傳紅血球半徑 `r0`，是所有尺寸門檻的尺度基準。\n"
    "- **`wbc_violet_mask(img)`**：白血球的紫羅蘭色遮罩。鎖定**窄色相窗 H∈[120,158]**，"
    "因為紅血球就算聚成一團仍偏粉紅，唯有白血球核是真紫色；飽和度放寬以兼顧淡染的核。\n"
    "- **`detect_wbc(img)`**：先以開運算 (opening) 只留下實心的核心、再小幅膨脹把分葉的核合併，"
    "最後用面積門檻濾掉血小板大小的紫點。**最先執行**，框出來後供其他細胞排除使用。\n"
    "- **`detect_rbc_rule(...)`**：自適應二值化取輪廓後，以面積、圓度、長寬比、尺寸層層過濾；"
    "中心落在白血球框內的候選一律捨棄，框半徑偏向 `r0` 以提高 IoU。\n"
    "- **`extract_platelet_components` / `detect_platelets_rule`**：用顆粒紋理（飽和度標準差、"
    "灰階標準差）把真血小板和均勻紫色雜訊分開，框固定大小以貼合一致的血小板標註。\n"
    "- **`watershed_*`**：分水嶺 + 距離轉換的加分項，用來切開沾黏的紅血球團（視覺化用）。"
))
cells.append(code("%%writefile blood_cell_detector.py\n" + detector_src))

cells.append(md(
    "## 2. 寫出 Streamlit App `app.py`\n"
    "\n"
    "`%%writefile` 會把這個 cell 的內容傾印成 `app.py`。這支 App 提供互動式介面：選擇影像、"
    "顯示前處理各階段、疊上預測框、列出三種細胞的計數與誤差，並可下載結果。"
))
cells.append(code("%%writefile app.py\n" + app_src))

cells.append(md(
    "## 3. 安裝相依套件\n"
    "\n"
    "只需要傳統影像處理會用到的套件，不含 scikit-learn（偵測為規則式，沒有模型）。"
))
cells.append(code(
    "import subprocess, sys\n"
    "\n"
    "# 偵測核心只靠 OpenCV + NumPy；scikit-image 僅供分水嶺加分階段使用。\n"
    "pkgs = [\n"
    "    'streamlit>=1.32',\n"
    "    'opencv-python-headless>=4.8',\n"
    "    'numpy>=1.24',\n"
    "    'pandas>=2.0',\n"
    "    'scikit-image>=0.21',  # 選用，僅用於分水嶺 (watershed) 加分階段\n"
    "    'pillow>=10.0',\n"
    "    'matplotlib>=3.7',\n"
    "]\n"
    "subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', *pkgs])\n"
    "print('相依套件安裝完成。')"
))

cells.append(md(
    "## 4. 取得 TXL-PBC 資料集（git clone）\n"
    "\n"
    "App 可以用內建的範例樣本執行，但評分 Demo 建議使用完整資料集，這樣才能切換 "
    "train / val / test。這裡直接從 GitHub 做淺層 clone（`--depth 1`），repo 已把影像與標註"
    "放在 `TXL-PBC/` 底下，不需要解壓縮。若資料集已存在則直接重用。"
))
cells.append(code(
    "import os, subprocess\n"
    "\n"
    "DATASET_REPO = 'https://github.com/lugan113/TXL-PBC_Dataset.git'\n"
    "\n"
    "# 不同執行環境的可能路徑，逐一嘗試。\n"
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
    "## 5. 快速健全性檢查\n"
    "\n"
    "拿 test 集第一張影像跑一次完整偵測流程，把預測計數和標註計數印出來對照，"
    "確認模組能正確 import、資料集路徑正確、偵測流程可運作。"
))
cells.append(code(
    "import os\n"
    "from blood_cell_detector import list_images, load_image, load_yolo_gt, detect_cells, count_boxes\n"
    "\n"
    "# 找出可用的資料集根目錄，找不到就退回內建樣本。\n"
    "root = None\n"
    "for candidate in ['TXL-PBC_Dataset/TXL-PBC', '/content/TXL-PBC_Dataset/TXL-PBC', './samples']:\n"
    "    if os.path.exists(os.path.join(candidate, 'images')) and os.path.exists(os.path.join(candidate, 'labels')):\n"
    "        root = candidate\n"
    "        break\n"
    "\n"
    "paths = list_images(root, 'test') if root else []\n"
    "print('根目錄:', root)\n"
    "print('test 影像數量:', len(paths))\n"
    "if paths:\n"
    "    img = load_image(paths[0])\n"
    "    # mode='Rule-based only' 走純規則式：先抓 WBC，再排除後分 RBC / 血小板。\n"
    "    preds = detect_cells(img, mode='Rule-based only')\n"
    "    gts = load_yolo_gt(paths[0], root)\n"
    "    print('範例影像:', os.path.basename(paths[0]))\n"
    "    print('標註計數 (GT):', count_boxes(gts))\n"
    "    print('預測計數 (Pred):', count_boxes(preds))"
))

cells.append(md(
    "## 6. 以 cloudflared 啟動 Streamlit\n"
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
