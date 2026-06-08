"""
Streamlit App for TXL-PBC classical blood-cell detection.

Run locally:
    streamlit run app.py

Run in Colab:
    Use TXL_PBC_Streamlit_Colab.ipynb in this package.
"""
from __future__ import annotations

import os
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import streamlit as st

from blood_cell_detector import (
    bgr_to_rgb,
    count_boxes,
    count_error_table,
    counts_to_csv_bytes,
    detect_cells,
    draw_boxes,
    draw_combined,
    encode_png,
    list_images,
    load_image,
    load_platelet_model,
    load_yolo_gt,
    predictions_to_csv_bytes,
    preprocess_pipeline,
)

st.set_page_config(page_title="TXL-PBC Classical Cell Counter", layout="wide")

APP_DIR = Path(__file__).resolve().parent
DEFAULT_FULL_ROOTS = [
    APP_DIR / "TXL-PBC",
    APP_DIR / "TXL-PBC_Dataset" / "TXL-PBC",
    Path("/content/TXL-PBC_Dataset/TXL-PBC"),
    Path("/content/TXL-PBC"),
    Path("/mnt/data/TXL-PBC_Dataset/TXL-PBC"),
]
SAMPLE_ROOT = APP_DIR / "samples"
MODEL_PATH = APP_DIR / "et_platelet_model.pkl"


@st.cache_resource(show_spinner=False)
def cached_model(model_path: str):
    return load_platelet_model(model_path)


def first_existing_root() -> Path:
    for root in DEFAULT_FULL_ROOTS:
        if (root / "images").exists() and (root / "labels").exists():
            return root
    return SAMPLE_ROOT


def valid_dataset_root(root: Path) -> bool:
    return (root / "images").exists() and (root / "labels").exists()


def percent_badge(value: float) -> str:
    return f"{value:.2f}%"


st.title("TXL-PBC Blood Smear Cell Counter - Classical CV Streamlit App")
st.caption("No deep learning is used. The pipeline uses grayscale, Gaussian blur, adaptive thresholding, morphology, area/circularity rules, optional watershed, and optional ExtraTrees on handcrafted platelet features.")

with st.sidebar:
    st.header("Data")
    default_root = first_existing_root()
    dataset_root_text = st.text_input("Dataset root", value=str(default_root), help="Folder containing images/train|val|test and labels/train|val|test. The packaged samples are used if the full dataset is unavailable.")
    dataset_root = Path(dataset_root_text).expanduser().resolve()
    if not valid_dataset_root(dataset_root):
        st.warning("Dataset root is invalid. Falling back to packaged samples.")
        dataset_root = SAMPLE_ROOT

    split = st.selectbox("Split", ["train", "val", "test"], index=2)
    image_paths = list_images(str(dataset_root), split)
    if not image_paths:
        st.error(f"No PNG images found under {dataset_root}/images/{split}")
        st.stop()

    image_names = [Path(p).name for p in image_paths]
    selected_name = st.selectbox("Image", image_names, index=0)
    img_path = image_paths[image_names.index(selected_name)]

    st.header("Detector")
    mode = st.selectbox(
        "Detection mode",
        ["Improved classical", "Rule-based only"],
        help="Improved classical uses ExtraTrees on handcrafted platelet features. Rule-based only uses area/circularity/color rules for all cell types.",
    )
    use_watershed = st.checkbox("Use Watershed RBC supplementation", value=False, help="Adds distance-transform watershed candidates for adjacent/overlapping RBCs. Useful for demo; may increase false positives on some images.")
    platelet_threshold = st.slider("Platelet ML threshold", 0.10, 0.95, 0.60, 0.05)

    st.header("Preprocessing parameters")
    gaussian_kernel = st.slider("Gaussian kernel", 3, 13, 5, 2)
    adaptive_block_ratio = st.slider("Adaptive block ratio", 0.70, 2.00, 1.25, 0.05)
    adaptive_c = st.slider("Adaptive threshold C", -5, 20, 5, 1)
    close_kernel = st.slider("Morphological closing kernel", 3, 21, 5, 2)
    rbc_min_circularity = st.slider("RBC min circularity", 0.02, 0.50, 0.08, 0.01)
    platelet_min_circularity = st.slider("Platelet min circularity - rule mode", 0.00, 0.80, 0.15, 0.01)

img = load_image(img_path)
gts = load_yolo_gt(img_path, str(dataset_root))
model = cached_model(str(MODEL_PATH)) if MODEL_PATH.exists() else None
preds = detect_cells(
    img,
    mode=mode,
    platelet_model=model,
    platelet_threshold=platelet_threshold,
    use_watershed=use_watershed,
    gaussian_kernel=gaussian_kernel,
    adaptive_block_ratio=adaptive_block_ratio,
    adaptive_c=adaptive_c,
    close_kernel=close_kernel,
    rbc_min_circularity=rbc_min_circularity,
    platelet_min_circularity=platelet_min_circularity,
)

st.subheader("Selected image")
info_cols = st.columns(4)
info_cols[0].metric("Split", split)
info_cols[1].metric("Image", selected_name[:18] + ("..." if len(selected_name) > 18 else ""))
info_cols[2].metric("GT total", len(gts))
info_cols[3].metric("Pred total", len(preds))

st.subheader("Ground Truth 與預測結果")
gt_img = draw_boxes(img, gts, prefix="GT")
pred_img = draw_boxes(img, preds, prefix="Pred")
left, right = st.columns(2)
with left:
    st.markdown("**Ground Truth**")
    st.image(bgr_to_rgb(gt_img), use_container_width=True)
with right:
    st.markdown("**Prediction**")
    st.image(bgr_to_rgb(pred_img), use_container_width=True)

st.subheader("Counts and error check")
count_rows = count_error_table(gts, preds)
count_df = pd.DataFrame(count_rows)
st.dataframe(count_df, hide_index=True, use_container_width=True)

c1, c2 = st.columns(2)
with c1:
    st.markdown("**Ground Truth counts**")
    st.json(count_boxes(gts))
with c2:
    st.markdown("**Prediction counts**")
    st.json(count_boxes(preds))

st.subheader("影像前處理 Pipeline visualization")
st.write("This section explicitly shows the required stages: Grayscale, Gaussian Blur, Adaptive Thresholding, and Morphological Closing. Watershed + Distance Transform is included for the bonus challenge.")
stages = preprocess_pipeline(
    img,
    gaussian_kernel=gaussian_kernel,
    adaptive_block_ratio=adaptive_block_ratio,
    adaptive_c=adaptive_c,
    close_kernel=close_kernel,
)
# Hide raw helper key from the grid.
visible_stage_names = [k for k in stages.keys() if not k.endswith("_raw")]
for row_start in range(0, len(visible_stage_names), 4):
    cols = st.columns(4)
    for col, name in zip(cols, visible_stage_names[row_start:row_start + 4]):
        with col:
            st.markdown(f"**{name}**")
            st.image(bgr_to_rgb(stages[name]), use_container_width=True)

st.subheader("Combined overlay and downloads")
combined = draw_combined(img, gts, preds)
st.image(bgr_to_rgb(combined), caption="Combined GT and Pred overlay", use_container_width=True)

d1, d2, d3 = st.columns(3)
with d1:
    st.download_button(
        "Download prediction overlay PNG",
        data=encode_png(pred_img),
        file_name=f"pred_{Path(selected_name).stem}.png",
        mime="image/png",
    )
with d2:
    st.download_button(
        "Download predictions CSV",
        data=predictions_to_csv_bytes(preds),
        file_name=f"pred_{Path(selected_name).stem}.csv",
        mime="text/csv",
    )
with d3:
    st.download_button(
        "Download count error CSV",
        data=counts_to_csv_bytes(count_rows),
        file_name=f"count_error_{Path(selected_name).stem}.csv",
        mime="text/csv",
    )

with st.expander("Implementation notes"):
    st.markdown(
        """
- **WBC:** purple/violet stain mask + dilation to merge fragmented nuclei + size/color rules.
- **RBC:** adaptive-threshold contour extraction + area, aspect ratio and circularity rules.
- **Platelet rule mode:** small purple connected components + area/circularity/color rules.
- **Improved classical mode:** platelet candidates are classified by ExtraTrees using handcrafted color, shape and local-context features. This is classical ML, not a deep neural network.
- **Watershed:** distance transform peaks are used as markers, then watershed boundaries are overlaid in red. The checkbox can add these candidates to RBC counting.
        """
    )
