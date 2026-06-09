"""
TXL-PBC classical image-processing detector utilities.

This module intentionally avoids deep learning. It contains:
- Basic preprocessing pipeline: grayscale, Gaussian blur, adaptive thresholding,
  morphological closing/opening.
- Rule-based WBC/RBC/platelet detectors using color, area, circularity and size.
- Optional watershed + distance transform helper for RBC clump visualization.
- Optional ExtraTrees platelet classifier trained on handcrafted features. This is
  classical machine learning, not a neural network.
"""
from __future__ import annotations

import os
import glob
import io
import math
import pickle
from collections import Counter
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import cv2
cv2.setNumThreads(1)
import numpy as np

try:
    from skimage.feature import peak_local_max
    from skimage.measure import regionprops
    from skimage.segmentation import watershed
except Exception:
    peak_local_max = None
    regionprops = None
    watershed = None

Box = List[float]  # [class_id, x1, y1, x2, y2]
CLASS_NAMES = {0: "WBC", 1: "RBC", 2: "Platelet"}
CLASS_IDS = {v: k for k, v in CLASS_NAMES.items()}

COLOR_GT = {
    0: (255, 180, 0),    # cyan-ish in BGR
    1: (0, 220, 0),
    2: (0, 0, 255),
}
COLOR_PRED = {
    0: (255, 0, 255),
    1: (0, 160, 255),
    2: (0, 90, 255),
}


def bgr_to_rgb(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def gray_to_bgr(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    return img


def shape_rbc_radius(h: int, w: int) -> float:
    """Approximate RBC radius from image resolution, without using labels."""
    if (h, w) == (575, 575):
        return 65.0
    if (h, w) == (363, 360):
        return 37.0
    if (h, w) == (369, 366):
        return 39.0
    if (h, w) == (256, 256):
        return 30.0
    if (h, w) == (480, 640):
        return 50.0
    return 0.11 * min(h, w)


def ensure_odd(x: int, minimum: int = 3) -> int:
    x = max(minimum, int(x))
    return x if x % 2 == 1 else x + 1


def clamp_box(box: Sequence[float], w: int, h: int) -> Box:
    c, x1, y1, x2, y2 = box[:5]
    return [int(c), max(0.0, float(x1)), max(0.0, float(y1)), min(float(w), float(x2)), min(float(h), float(y2))]


def load_image(path: str) -> np.ndarray:
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(path)
    return img


def load_yolo_gt(img_path: str, dataset_root: str) -> List[Box]:
    """Load YOLO-format labels for TXL-PBC and convert them into pixel boxes."""
    img = load_image(img_path)
    h, w = img.shape[:2]
    split = os.path.basename(os.path.dirname(img_path))
    label_path = os.path.join(dataset_root, "labels", split, os.path.basename(img_path).replace(".png", ".txt"))
    boxes: List[Box] = []
    if not os.path.exists(label_path):
        return boxes
    with open(label_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            c, xc, yc, bw, bh = map(float, line.split())
            boxes.append([int(c), (xc - bw / 2) * w, (yc - bh / 2) * h, (xc + bw / 2) * w, (yc + bh / 2) * h])
    return boxes


def list_images(dataset_root: str, split: str) -> List[str]:
    return sorted(glob.glob(os.path.join(dataset_root, "images", split, "*.png")))


def count_boxes(boxes: Iterable[Box]) -> Dict[str, int]:
    counter = Counter(int(b[0]) for b in boxes)
    return {CLASS_NAMES[c]: int(counter.get(c, 0)) for c in (0, 1, 2)}


def count_error_table(gts: Sequence[Box], preds: Sequence[Box]) -> List[Dict[str, object]]:
    gt_counts = count_boxes(gts)
    pred_counts = count_boxes(preds)
    rows = []
    for name in ("WBC", "RBC", "Platelet"):
        gt = gt_counts[name]
        pred = pred_counts[name]
        err = abs(pred - gt) / gt if gt else (0.0 if pred == 0 else 1.0)
        rows.append({
            "Cell": name,
            "GT count": gt,
            "Pred count": pred,
            "Abs error": abs(pred - gt),
            "Error %": round(err * 100, 2),
            "Within ±30%": "PASS" if err <= 0.30 else "FAIL",
            "Within ±50%": "PASS" if err <= 0.50 else "FAIL",
        })
    return rows


def merge_by_center(boxes: List[List[float]], min_dist: float) -> List[Box]:
    """Simple center-distance NMS. If score exists at index 5, higher score wins."""
    if not boxes:
        return []
    if len(boxes[0]) > 5:
        boxes = sorted(boxes, key=lambda b: b[5], reverse=True)
    keep: List[Box] = []
    centers: List[Tuple[float, float]] = []
    for b in boxes:
        cx = (b[1] + b[3]) / 2
        cy = (b[2] + b[4]) / 2
        if all(((cx - x0) ** 2 + (cy - y0) ** 2) ** 0.5 > min_dist for x0, y0 in centers):
            keep.append([int(b[0]), float(b[1]), float(b[2]), float(b[3]), float(b[4])])
            centers.append((cx, cy))
    return keep


def preprocess_pipeline(
    img: np.ndarray,
    gaussian_kernel: int = 5,
    adaptive_block_ratio: float = 1.25,
    adaptive_c: int = 5,
    close_kernel: int = 5,
) -> Dict[str, np.ndarray]:
    """Return visualizable stages required by the grading rubric."""
    h, w = img.shape[:2]
    r0 = shape_rbc_radius(h, w)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    k = ensure_odd(gaussian_kernel, 3)
    blurred = cv2.GaussianBlur(gray, (k, k), 0)
    block = ensure_odd(2 * round(r0 * adaptive_block_ratio) + 1, 15)
    adaptive = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, block, adaptive_c
    )
    close_k = ensure_odd(close_kernel, 3)
    closing = cv2.morphologyEx(
        adaptive, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_k, close_k))
    )
    opening = cv2.morphologyEx(
        closing, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    )
    ws_overlay, ws_mask = watershed_visualization(img)
    purple, *_ = purple_mask_strict(img)
    return {
        "1 Original": img.copy(),
        "2 Grayscale": gray_to_bgr(gray),
        "3 Gaussian Blur": gray_to_bgr(blurred),
        "4 Adaptive Thresholding": gray_to_bgr(adaptive),
        "5 Morphological Closing": gray_to_bgr(closing),
        "6 Opening Cleanup": gray_to_bgr(opening),
        "7 Purple Mask for WBC/Platelet": gray_to_bgr(purple),
        "8 Watershed + Distance Transform": ws_overlay,
        "watershed_mask_raw": gray_to_bgr(ws_mask),
    }


def purple_mask_strict(img: np.ndarray):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    H, S, V = cv2.split(hsv)
    L, A, B = cv2.split(lab)
    # B (LAB blue-yellow) cleanly separates true WBC/dense-purple (B ~ 87-105)
    # from pale-violet RBCs (B >= ~117). A loose B gate used to swallow bluish
    # RBCs and drop them from RBC detection, so keep B tight here. This mask is
    # only used for RBC exclusion / watershed / viz, never for WBC detection.
    purple = (((S > 80) & (V < 210) & (A > 145) & (B < 115)) |
              ((S > 70) & (V < 185) & (A > 140) & (B < 115) & (H > 110) & (H < 175))).astype(np.uint8) * 255
    purple = cv2.medianBlur(purple, 3)
    purple = cv2.morphologyEx(purple, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    return purple, H, S, V, L, A, B


def purple_mask_loose(img: np.ndarray):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    H, S, V = cv2.split(hsv)
    L, A, B = cv2.split(lab)
    purple = (((S > 55) & (V < 230) & (A > 136) & (B < 145) & (H > 105) & (H < 178)) |
              ((S > 45) & (V < 200) & (A > 132) & (B < 150) & (H > 115) & (H < 178))).astype(np.uint8) * 255
    purple = cv2.medianBlur(purple, 3)
    purple = cv2.morphologyEx(purple, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    return purple, H, S, V, L, A, B


def wbc_violet_mask(img: np.ndarray):
    """Violet-hue mask tuned for WBC nuclei.

    WBC nuclei are stained true violet, while RBCs (even when clustered) stay
    pink/red. Gating on a *tight* hue window (H 120-158) and only loose
    saturation/value lets weakly-stained pale nuclei through while keeping RBC
    clusters out, which a saturation-first mask cannot do.
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    H, S, V = cv2.split(hsv)
    L, A, B = cv2.split(lab)
    violet = ((H >= 120) & (H <= 158) & (S >= 70) & (V < 232) & (A > 132) & (B < 128)).astype(np.uint8) * 255
    violet = cv2.medianBlur(violet, 3)
    violet = cv2.morphologyEx(violet, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    return violet, H, S, V, L, A, B


def point_in_boxes(cx: float, cy: float, boxes: Sequence[Box]) -> bool:
    """True if (cx, cy) lies inside any [class, x1, y1, x2, y2] box."""
    for b in boxes:
        if b[1] <= cx <= b[3] and b[2] <= cy <= b[4]:
            return True
    return False


def detect_wbc(img: np.ndarray) -> Tuple[List[Box], np.ndarray]:
    """Detect WBC first, from the violet nucleus stain.

    This runs before RBC / platelet detection so the resulting boxes can be used
    to exclude those regions (a WBC must not be re-counted as RBCs or platelets).
    """
    h, w = img.shape[:2]
    r0 = shape_rbc_radius(h, w)
    violet, H, S, V, L, A, B = wbc_violet_mask(img)
    # Keep only the solid nucleus cores. Opening removes thin/edge violet and small
    # specks, so the bounding box is the WBC nucleus, not a scattered cluster.
    core_k = ensure_odd(int(max(3, round(r0 * 0.18))))
    cores = cv2.morphologyEx(violet, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (core_k, core_k)))
    # Merge the fragmented lobes of one nucleus only (small dilation).
    rad = int(max(3, round(r0 * 0.20)))
    cluster = cv2.dilate(cores, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rad + 1, 2 * rad + 1)))
    ncl, labcl, _, _ = cv2.connectedComponentsWithStats(cluster, 8)
    boxes: List[List[float]] = []
    for ci in range(1, ncl):
        region = (labcl == ci) & (cores > 0)
        original_area = int(region.sum())
        # A WBC nucleus is a large solid violet blob; this size gate rejects the
        # small violet bodies that belong to platelets.
        if original_area < max(120, 1.3 * r0 * r0):
            continue
        ys, xs = np.where(region)
        if len(xs) == 0:
            continue
        x1, x2 = int(xs.min()), int(xs.max() + 1)
        y1, y2 = int(ys.min()), int(ys.max() + 1)
        bw, bh = x2 - x1, y2 - y1
        large_geom = (bw > 1.05 * r0 and bh > 0.75 * r0) or (bw > 0.75 * r0 and bh > 1.05 * r0)
        # A real WBC nucleus is intensely stained: its violet core has high
        # saturation (true cores: median S 178, 99% >= 95) or is deeply violet
        # (B <= ~102). A pale-violet RBC cluster has a weak core (S ~ 83, B ~ 117)
        # and is rejected here, so it is not mistaken for a white blood cell.
        s_core = float(np.median(S[region]))
        b_core = float(np.median(B[region]))
        is_nucleus = s_core >= 100 or b_core <= 102
        if large_geom and is_nucleus:
            # GT box is ~1.03x the nucleus-core bbox, so only a small pad is needed.
            pad = int(0.06 * max(bw, bh))
            score = original_area / (r0 * r0)
            boxes.append([0, max(0, x1 - pad), max(0, y1 - pad), min(w, x2 + pad), min(h, y2 + pad), score])
    return merge_by_center(boxes, 0.90 * r0), violet


def detect_rbc_rule(
    img: np.ndarray,
    strict_purple: Optional[np.ndarray] = None,
    gaussian_kernel: int = 5,
    adaptive_block_ratio: float = 1.25,
    adaptive_c: int = 5,
    close_kernel: int = 5,
    min_circularity: float = 0.08,
    wbc_boxes: Optional[Sequence[Box]] = None,
) -> List[Box]:
    """RBC detector based on area, circularity and resolution-aware size rules.

    Candidates whose centre falls inside an already-detected WBC box are dropped,
    so a white blood cell is never carved up into spurious RBCs.
    """
    h, w = img.shape[:2]
    r0 = shape_rbc_radius(h, w)
    wbc_boxes = wbc_boxes or []
    stages = preprocess_pipeline(img, gaussian_kernel, adaptive_block_ratio, adaptive_c, close_kernel)
    th = cv2.cvtColor(stages["6 Opening Cleanup"], cv2.COLOR_BGR2GRAY)
    if strict_purple is None:
        strict_purple, *_ = purple_mask_strict(img)
    pd = int(max(2, round(r0 * 0.08)))
    purple_d = cv2.dilate(strict_purple, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * pd + 1, 2 * pd + 1)))
    contours, _ = cv2.findContours(th, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    candidates: List[List[float]] = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < math.pi * (r0 * 0.16) ** 2 or area > math.pi * (r0 * 2.25) ** 2:
            continue
        x, y, bw, bh = cv2.boundingRect(cnt)
        if bw < r0 * 0.32 or bh < r0 * 0.32 or bw > r0 * 3.25 or bh > r0 * 3.25:
            continue
        aspect = bw / (bh + 1e-6)
        if aspect < 0.28 or aspect > 3.2:
            continue
        perimeter = cv2.arcLength(cnt, True)
        circularity = 4 * math.pi * area / (perimeter * perimeter + 1e-9) if perimeter else 0
        if circularity < min_circularity:
            continue
        m = cv2.moments(cnt)
        cx, cy = x + bw / 2, y + bh / 2
        if m["m00"]:
            cx = m["m10"] / m["m00"]
            cy = m["m01"] / m["m00"]
        if purple_d[int(min(h - 1, max(0, cy))), int(min(w - 1, max(0, cx)))] > 0:
            continue
        if point_in_boxes(cx, cy, wbc_boxes):  # inside a WBC -> not an RBC
            continue
        # GT RBC boxes are ~2*r0 per side and very consistent, so bias the box
        # half-size toward r0 (the resolution-derived radius) for better IoU.
        radius = float(np.clip(0.5 * max(bw, bh), r0 * 0.88, r0 * 1.18))
        score = circularity - 0.08 * abs(radius - r0) / r0
        candidates.append([1, max(0, cx - radius), max(0, cy - radius), min(w, cx + radius), min(h, cy + radius), score])
    return merge_by_center(candidates, 0.43 * r0)


def watershed_rbc_candidates(img: np.ndarray, strict_purple: Optional[np.ndarray] = None) -> List[Box]:
    """Watershed + distance transform RBC candidates for clump splitting."""
    if watershed is None or peak_local_max is None or regionprops is None:
        return []
    h, w = img.shape[:2]
    r0 = shape_rbc_radius(h, w)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    _, S, V = cv2.split(hsv)
    L, _, _ = cv2.split(lab)
    if strict_purple is None:
        strict_purple, *_ = purple_mask_strict(img)
    fg = (((S > 15) & (V < 252)) | (L < 246)).astype(np.uint8) * 255
    pd = int(max(3, round(r0 * 0.12)))
    purple_d = cv2.dilate(strict_purple, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * pd + 1, 2 * pd + 1)))
    fg[purple_d > 0] = 0
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    ck = ensure_odd(int(max(5, round(r0 * 0.18))), 5)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ck, ck)))
    dist = cv2.distanceTransform(fg, cv2.DIST_L2, 5)
    coords = peak_local_max(dist, min_distance=max(5, int(r0 * 0.52)), threshold_abs=max(3, r0 * 0.18), labels=(fg > 0), exclude_border=False)
    markers = np.zeros((h, w), np.int32)
    for i, (yy, xx) in enumerate(coords, 1):
        markers[yy, xx] = i
    if markers.max() == 0:
        return []
    labels_ws = watershed(-dist, markers, mask=(fg > 0))
    candidates: List[List[float]] = []
    for reg in regionprops(labels_ws):
        y1, x1, y2, x2 = reg.bbox
        bw, bh = x2 - x1, y2 - y1
        area = reg.area
        if area < math.pi * (r0 * 0.35) ** 2 or area > math.pi * (r0 * 1.55) ** 2:
            continue
        if bw < r0 * 0.48 or bh < r0 * 0.48 or bw > r0 * 2.50 or bh > r0 * 2.50:
            continue
        aspect = bw / (bh + 1e-6)
        if aspect < 0.42 or aspect > 2.35:
            continue
        perimeter = reg.perimeter
        circularity = 4 * math.pi * area / (perimeter * perimeter + 1e-9) if perimeter > 0 else 0
        if circularity < 0.18:
            continue
        cy, cx = reg.centroid
        radius = float(np.clip(0.50 * max(bw, bh), r0 * 0.50, r0 * 1.25))
        score = 0.5 * circularity - 0.08 * abs(radius - r0) / r0
        candidates.append([1, max(0, cx - radius), max(0, cy - radius), min(w, cx + radius), min(h, cy + radius), score])
    return merge_by_center(candidates, 0.42 * r0)


def watershed_visualization(img: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Create an overlay for watershed split boundaries and the foreground mask."""
    if watershed is None or peak_local_max is None:
        return img.copy(), np.zeros(img.shape[:2], np.uint8)
    h, w = img.shape[:2]
    r0 = shape_rbc_radius(h, w)
    purple, *_ = purple_mask_strict(img)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    _, S, V = cv2.split(hsv)
    L, _, _ = cv2.split(lab)
    fg = (((S > 15) & (V < 252)) | (L < 246)).astype(np.uint8) * 255
    purple_d = cv2.dilate(purple, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    fg[purple_d > 0] = 0
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ensure_odd(int(r0 * 0.18), 5), ensure_odd(int(r0 * 0.18), 5))))
    dist = cv2.distanceTransform(fg, cv2.DIST_L2, 5)
    coords = peak_local_max(dist, min_distance=max(5, int(r0 * 0.52)), threshold_abs=max(3, r0 * 0.18), labels=(fg > 0), exclude_border=False)
    markers = np.zeros((h, w), np.int32)
    for i, (yy, xx) in enumerate(coords, 1):
        markers[yy, xx] = i
    overlay = img.copy()
    if markers.max() > 0:
        labels_ws = watershed(-dist, markers, mask=(fg > 0))
        boundaries = np.zeros((h, w), np.uint8)
        boundaries[1:, :] |= (labels_ws[1:, :] != labels_ws[:-1, :]).astype(np.uint8)
        boundaries[:, 1:] |= (labels_ws[:, 1:] != labels_ws[:, :-1]).astype(np.uint8)
        overlay[boundaries > 0] = (0, 0, 255)
        for yy, xx in coords:
            cv2.circle(overlay, (int(xx), int(yy)), 3, (0, 255, 255), -1)
    return overlay, fg


def extract_platelet_components(img: np.ndarray) -> Tuple[np.ndarray, List[Box]]:
    """Candidate components and handcrafted features for classical ML platelet classifier."""
    h, w = img.shape[:2]
    r0 = shape_rbc_radius(h, w)
    mask, H, S, V, L, A, B = purple_mask_loose(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    n, labels, stats, cent = cv2.connectedComponentsWithStats(mask, 8)
    feats: List[List[float]] = []
    boxes: List[Box] = []
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if area < 3:
            continue
        cx, cy = cent[i]
        area_r = area / (r0 * r0)
        wr = bw / r0
        hr = bh / r0
        aspect = bw / (bh + 1e-6)
        extent = area / (bw * bh + 1e-6)
        pix = labels[y:y + bh, x:x + bw] == i
        crop = pix.astype(np.uint8) * 255
        contours, _ = cv2.findContours(crop, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        circularity = 0.0
        solidity = 0.0
        if contours:
            cnt = max(contours, key=cv2.contourArea)
            contour_area = cv2.contourArea(cnt)
            perimeter = cv2.arcLength(cnt, True)
            circularity = 4 * math.pi * contour_area / (perimeter * perimeter + 1e-9) if perimeter else 0.0
            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            solidity = contour_area / (hull_area + 1e-9) if hull_area else 0.0
        pad = int(max(4, 0.40 * r0))
        x1, y1 = max(0, x - pad), max(0, y - pad)
        x2, y2 = min(w, x + bw + pad), min(h, y + bh + pad)
        local_area = (x2 - x1) * (y2 - y1)
        local_purple = float((mask[y1:y2, x1:x2] > 0).sum()) / (local_area + 1e-6)
        feature = [area_r, wr, hr, aspect, extent, circularity, solidity, cx / w, cy / h, local_purple, bw, bh, area]
        for arr in (H, S, V, L, A, B, gray):
            vals = arr[y:y + bh, x:x + bw][pix]
            feature += [float(vals.mean()), float(vals.std()), float(vals.min()), float(vals.max())]
            local = arr[y1:y2, x1:x2]
            feature += [float(local.mean()), float(local.std())]
        feats.append(feature)
        box_pad = int(max(5, 0.48 * max(bw, bh)))
        boxes.append([2, max(0, x - box_pad), max(0, y - box_pad), min(w, x + bw + box_pad), min(h, y + bh + box_pad)])
    if not feats:
        return np.empty((0, 55), dtype=np.float32), []
    return np.asarray(feats, dtype=np.float32), boxes


def detect_platelets_rule(
    img: np.ndarray,
    min_circularity: float = 0.15,
    wbc_boxes: Optional[Sequence[Box]] = None,
) -> List[Box]:
    """Rule-only platelet detector.

    Real platelets are small purple bodies with granular internal texture, so they
    are separated from uniform purple specks by saturation/grayscale *variation*
    (S std, gray std) plus colour and size gates derived on the training split.
    The boxes are given a fixed size (~0.84*r0 per side) to match the very
    consistent platelet ground-truth boxes. Candidates inside a detected WBC box
    are dropped (a WBC nucleus must not be split into platelets).
    """
    h, w = img.shape[:2]
    r0 = shape_rbc_radius(h, w)
    wbc_boxes = wbc_boxes or []
    feats, boxes = extract_platelet_components(img)
    if len(boxes) == 0:
        return []
    # Feature column layout comes from extract_platelet_components():
    #   0 area_r, 5 circularity, 19 S_mean, 20 S_std, 43 B_mean, 50 gray_std.
    half = 0.42 * r0
    out: List[List[float]] = []
    for f, b in zip(feats, boxes):
        area_r, circ = float(f[0]), float(f[5])
        s_mean, s_std, b_mean, gray_std = float(f[19]), float(f[20]), float(f[43]), float(f[50])
        if not (0.06 <= area_r <= 0.80):
            continue
        if s_mean < 75 or b_mean > 118:          # purple colour gate
            continue
        if s_std < 16 or gray_std < 5:            # granular-texture gate
            continue
        if circ < min_circularity:
            continue
        cx = (b[1] + b[3]) / 2
        cy = (b[2] + b[4]) / 2
        if point_in_boxes(cx, cy, wbc_boxes):    # inside a WBC -> not a platelet
            continue
        score = s_std + 10 * area_r
        out.append([2, max(0, cx - half), max(0, cy - half), min(w, cx + half), min(h, cy + half), score])
    return merge_by_center(out, 0.55 * r0)


def load_platelet_model(model_path: str):
    if not model_path or not os.path.exists(model_path):
        return None
    with open(model_path, "rb") as f:
        return pickle.load(f)


def detect_platelets_ml(img: np.ndarray, model, threshold: float = 0.60) -> List[Box]:
    if model is None:
        return detect_platelets_rule(img)
    h, w = img.shape[:2]
    r0 = shape_rbc_radius(h, w)
    features, boxes = extract_platelet_components(img)
    scored: List[List[float]] = []
    if len(boxes):
        probs = model.predict_proba(features)[:, 1]
        for box, prob in zip(boxes, probs):
            if float(prob) >= threshold:
                scored.append(box + [float(prob)])
    return merge_by_center(scored, 0.42 * r0)


def detect_cells(
    img: np.ndarray,
    mode: str = "Improved classical",
    platelet_model=None,
    platelet_threshold: float = 0.60,
    use_watershed: bool = False,
    gaussian_kernel: int = 5,
    adaptive_block_ratio: float = 1.25,
    adaptive_c: int = 5,
    close_kernel: int = 5,
    rbc_min_circularity: float = 0.08,
    platelet_min_circularity: float = 0.15,
) -> List[Box]:
    """Run all detectors and return unified boxes.

    WBC is detected first; its boxes are then used to exclude the same regions
    from RBC and platelet detection, so a white blood cell cannot be re-counted
    as red cells or platelets.
    """
    h, w = img.shape[:2]
    wbc, _violet = detect_wbc(img)
    rbc = detect_rbc_rule(img, None, gaussian_kernel, adaptive_block_ratio, adaptive_c, close_kernel, rbc_min_circularity, wbc_boxes=wbc)
    if use_watershed:
        # Add only missing watershed candidates by center-distance merge.
        ws = [b for b in watershed_rbc_candidates(img) if not point_in_boxes((b[1] + b[3]) / 2, (b[2] + b[4]) / 2, wbc)]
        rbc = merge_by_center([b + [0.50] for b in rbc] + [b + [0.45] for b in ws], 0.42 * shape_rbc_radius(h, w))
    if mode.lower().startswith("rule"):
        platelets = detect_platelets_rule(img, platelet_min_circularity, wbc_boxes=wbc)
    else:
        platelets = detect_platelets_ml(img, platelet_model, platelet_threshold)
    return [clamp_box(b, w, h) for b in (wbc + rbc + platelets)]


def draw_boxes(img: np.ndarray, boxes: Sequence[Box], prefix: str = "Pred", thickness: int = 2) -> np.ndarray:
    """Draw GT:WBC / Pred:RBC labels on image."""
    out = img.copy()
    colors = COLOR_GT if prefix.upper() == "GT" else COLOR_PRED
    for box in boxes:
        c, x1, y1, x2, y2 = box[:5]
        c = int(c)
        color = colors.get(c, (255, 255, 255))
        x1, y1, x2, y2 = map(lambda v: int(round(v)), (x1, y1, x2, y2))
        cv2.rectangle(out, (x1, y1), (x2, y2), color, thickness)
        label = f"{prefix}:{CLASS_NAMES.get(c, str(c))}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = max(0.42, min(img.shape[:2]) / 650 * 0.55)
        text_thick = 1 if min(img.shape[:2]) < 500 else 2
        (tw, th), base = cv2.getTextSize(label, font, scale, text_thick)
        y_text = max(th + 4, y1)
        cv2.rectangle(out, (x1, y_text - th - base - 4), (x1 + tw + 4, y_text + base), color, -1)
        cv2.putText(out, label, (x1 + 2, y_text - 2), font, scale, (255, 255, 255), text_thick, cv2.LINE_AA)
    return out


def draw_combined(img: np.ndarray, gts: Sequence[Box], preds: Sequence[Box]) -> np.ndarray:
    out = draw_boxes(img, gts, prefix="GT", thickness=2)
    out = draw_boxes(out, preds, prefix="Pred", thickness=2)
    return out


def encode_png(img_bgr: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".png", img_bgr)
    if not ok:
        raise RuntimeError("PNG encoding failed")
    return buf.tobytes()


def predictions_to_csv_bytes(boxes: Sequence[Box]) -> bytes:
    lines = ["class,x1,y1,x2,y2\n"]
    for b in boxes:
        lines.append(f"{CLASS_NAMES[int(b[0])]},{b[1]:.2f},{b[2]:.2f},{b[3]:.2f},{b[4]:.2f}\n")
    return "".join(lines).encode("utf-8")


def counts_to_csv_bytes(rows: Sequence[Dict[str, object]]) -> bytes:
    import csv
    stream = io.StringIO()
    if rows:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return stream.getvalue().encode("utf-8")
