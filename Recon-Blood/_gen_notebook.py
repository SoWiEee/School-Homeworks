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
    "# TXL-PBC Classical Blood Cell Counter - Self-contained Colab notebook\n"
    "\n"
    "This single notebook is fully self-contained. Running the cells top to bottom will:\n"
    "\n"
    "1. Write the project source files (`blood_cell_detector.py`, `app.py`) to disk via `%%writefile`.\n"
    "2. Install the required dependencies.\n"
    "3. Clone the TXL-PBC dataset from GitHub.\n"
    "4. Launch the Streamlit App through a temporary Cloudflare tunnel.\n"
    "\n"
    "No project upload and no model file are required. Detection is fully rule-based "
    "(classical image processing only, no deep learning and no trained model)."
))

cells.append(md(
    "## 1. Write the detector module\n"
    "\n"
    "`%%writefile` dumps this cell to `blood_cell_detector.py` so the App can import it."
))
cells.append(code("%%writefile blood_cell_detector.py\n" + detector_src))

cells.append(md(
    "## 2. Write the Streamlit App\n"
    "\n"
    "`%%writefile` dumps this cell to `app.py`."
))
cells.append(code("%%writefile app.py\n" + app_src))

cells.append(md("## 3. Install dependencies"))
cells.append(code(
    "import subprocess, sys\n"
    "\n"
    "pkgs = [\n"
    "    'streamlit>=1.32',\n"
    "    'opencv-python-headless>=4.8',\n"
    "    'numpy>=1.24',\n"
    "    'pandas>=2.0',\n"
    "    'scikit-image>=0.21',  # optional, only for the watershed bonus stage\n"
    "    'pillow>=10.0',\n"
    "    'matplotlib>=3.7',\n"
    "]\n"
    "subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', *pkgs])\n"
    "print('Dependencies installed.')"
))

cells.append(md(
    "## 4. Get the TXL-PBC dataset (git clone)\n"
    "\n"
    "The App can run with packaged samples, but the grading demo should use the full "
    "dataset so train / val / test selection works. This shallow-clones the dataset "
    "directly from GitHub. The repo stores images and labels directly under `TXL-PBC/`, "
    "so no unzip step is needed. If the dataset is already present, it is reused."
))
cells.append(code(
    "import os, subprocess\n"
    "\n"
    "DATASET_REPO = 'https://github.com/lugan113/TXL-PBC_Dataset.git'\n"
    "\n"
    "CANDIDATE_ROOTS = [\n"
    "    'TXL-PBC_Dataset/TXL-PBC',\n"
    "    './TXL-PBC_Dataset/TXL-PBC',\n"
    "    '/content/TXL-PBC_Dataset/TXL-PBC',\n"
    "]\n"
    "\n"
    "def find_dataset():\n"
    "    for root in CANDIDATE_ROOTS:\n"
    "        if os.path.exists(os.path.join(root, 'images')) and os.path.exists(os.path.join(root, 'labels')):\n"
    "            return root\n"
    "    return None\n"
    "\n"
    "root = find_dataset()\n"
    "if root is None:\n"
    "    print('Cloning TXL-PBC dataset (shallow)...')\n"
    "    subprocess.check_call(['git', 'clone', '--depth', '1', DATASET_REPO, 'TXL-PBC_Dataset'])\n"
    "    root = find_dataset()\n"
    "\n"
    "print('Dataset root:', root if root else 'not found; the App will fall back to packaged samples')"
))

cells.append(md("## 5. Quick sanity check"))
cells.append(code(
    "import os\n"
    "from blood_cell_detector import list_images, load_image, load_yolo_gt, detect_cells, count_boxes\n"
    "\n"
    "root = None\n"
    "for candidate in ['TXL-PBC_Dataset/TXL-PBC', '/content/TXL-PBC_Dataset/TXL-PBC', './samples']:\n"
    "    if os.path.exists(os.path.join(candidate, 'images')) and os.path.exists(os.path.join(candidate, 'labels')):\n"
    "        root = candidate\n"
    "        break\n"
    "\n"
    "paths = list_images(root, 'test') if root else []\n"
    "print('Root:', root)\n"
    "print('Number of test images:', len(paths))\n"
    "if paths:\n"
    "    img = load_image(paths[0])\n"
    "    preds = detect_cells(img, mode='Rule-based only')\n"
    "    gts = load_yolo_gt(paths[0], root)\n"
    "    print('Example image:', os.path.basename(paths[0]))\n"
    "    print('GT counts:', count_boxes(gts))\n"
    "    print('Pred counts:', count_boxes(preds))"
))

cells.append(md(
    "## 6. Launch Streamlit with cloudflared\n"
    "\n"
    "Run this cell and open the printed public URL. Keep this notebook running while using the App."
))
cells.append(code(
    "import subprocess, time, re, os\n"
    "\n"
    "CF_URL = 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64'\n"
    "CF_BIN = './cloudflared'\n"
    "\n"
    "# Stop old app/tunnel processes if this cell is re-run.\n"
    "for name in ['streamlit_proc', 'cf_proc']:\n"
    "    proc = globals().get(name)\n"
    "    if proc is not None and proc.poll() is None:\n"
    "        proc.terminate()\n"
    "        time.sleep(1)\n"
    "\n"
    "# Download cloudflared. If wget fails, fall back to curl.\n"
    "if not os.path.exists(CF_BIN):\n"
    "    print('Downloading cloudflared...')\n"
    "    ok = subprocess.run(['wget', '-q', CF_URL, '-O', CF_BIN]).returncode == 0\n"
    "    if not ok:\n"
    "        ok = subprocess.run(['curl', '-sL', CF_URL, '-o', CF_BIN]).returncode == 0\n"
    "    if not ok:\n"
    "        raise RuntimeError('cloudflared download failed. Check network settings or use Colab port forwarding instead.')\n"
    "    subprocess.run(['chmod', '+x', CF_BIN])\n"
    "    print('cloudflared downloaded.')\n"
    "\n"
    "# Launch Streamlit in the background.\n"
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
    "# Start Cloudflare tunnel and parse the public URL from stderr.\n"
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
    "print('Streamlit App started.')\n"
    "print(f'Public URL: {url}')\n"
    "print('Open the URL above to use the interactive App.')"
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
