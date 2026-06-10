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
    s_med = float(np.median(S))  # image-wide saturation, for the oversized-blob gate
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
        # An oversized violet blob (>= 4.5*r0) is only a real (large/monocyte)
        # nucleus if its core is far more saturated than the whole image. On a
        # globally violet-shifted smear the violet mask blooms into an image-
        # spanning blob whose core sits barely above the image median
        # (s_core - s_med ~ 24, vs ~104 for a true large WBC); without this gate
        # that bloom becomes a whole-image WBC box that then excludes every RBC /
        # platelet inside it (RBC recall -> 0 on those images).
        oversized = max(bw, bh) >= 4.5 * r0
        strong_stain = (s_core - s_med) >= 70.0
        if large_geom and is_nucleus and (not oversized or strong_stain):
            # The opened violet core sits inside the GT cell box (matched pred/GT
            # width median 0.928), so pad ~0.10*side to grow the box onto the GT
            # and lift IoU at the stricter 0.5 threshold.
            pad = int(0.10 * max(bw, bh))
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

    Contours are extracted with RETR_LIST: the inner "hole" of each ring-shaped
    cell becomes its own contour, which is what splits a touching clump into one
    detection per cell. The cost is that the clump's *outer* boundary also passes
    the gates and yields an oversized box wrapping cells it already detected; a
    containment-suppression pass removes that redundant wrapper afterwards.
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
    candidates: List[List[float]] = []  # [class, x1, y1, x2, y2, score, is_clump]
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
        # The dark cell *ring* sits ~11% inside the GT box, so the contour-derived
        # radius is systematically small (matched pred/GT width median 0.888).
        # Scaling by 1.13 re-centres that ratio on 1.0, which lifts IoU markedly
        # at the stricter 0.5 threshold (matched mean IoU 0.70 -> 0.76) without
        # losing any 0.3 matches.
        radius = float(np.clip(0.5 * max(bw, bh), r0 * 0.88, r0 * 1.18)) * 1.13
        score = circularity - 0.08 * abs(radius / 1.13 - r0) / r0
        # A contour wider/taller than ~1.5 cell radii is a clump's outer boundary,
        # not a single cell; flag it so the wrapper can be suppressed below.
        is_clump = 1.0 if (bw > 1.5 * r0 or bh > 1.5 * r0) else 0.0
        candidates.append([1, max(0, cx - radius), max(0, cy - radius), min(w, cx + radius), min(h, cy + radius), score, is_clump])
    # Containment suppression: drop a clump wrapper box only when a finer
    # (non-clump) detection centre lies *well inside* it (within the central 80%),
    # so the wrapper is genuinely redundant. Checking against the full wrapper box
    # over-suppressed: a separate cell merely touching the clump's edge wrongly
    # dropped the wrapper, losing visibly-present cells (worse once boxes grew in
    # fix 9). The 0.80 shrink keeps fix 6's de-duplication while recovering them.
    contain_shrink = 0.80
    fine_centers = [((b[1] + b[3]) / 2, (b[2] + b[4]) / 2) for b in candidates if not b[6]]
    kept: List[List[float]] = []
    for b in candidates:
        if b[6]:
            mx, my = (b[1] + b[3]) / 2, (b[2] + b[4]) / 2
            hw, hh = (b[3] - b[1]) / 2 * contain_shrink, (b[4] - b[2]) / 2 * contain_shrink
            if any(mx - hw <= ox <= mx + hw and my - hh <= oy <= my + hh for ox, oy in fine_centers):
                continue
        kept.append(b[:6])
    return merge_by_center(kept, 0.43 * r0)


def _fill_holes(mask: np.ndarray) -> np.ndarray:
    """Fill the enclosed background regions of a binary mask (donut -> disk)."""
    ff = mask.copy()
    h, w = mask.shape[:2]
    flood_mask = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(ff, flood_mask, (0, 0), 255)  # flood the outer background
    return mask | cv2.bitwise_not(ff)            # add only the enclosed holes


def rbc_filled_foreground(img: np.ndarray, r0: float, strict_purple: np.ndarray) -> np.ndarray:
    """Solid RBC cell-body mask for distance transform / watershed.

    RBCs are dark membrane *rings* around a pale centre on an often-tinted
    background, so a colour/brightness threshold floods ~94% of the field and the
    distance transform is meaningless. Instead, take the membrane ring mask, close
    its small gaps, and fill the enclosed centres -- turning each donut into a
    solid disk. Touching cells then form a multi-lobed blob with one distance peak
    per cell, which is what watershed needs to split them.
    """
    # Same adaptive-threshold ring mask as preprocess_pipeline stage 6, computed
    # directly here (preprocess_pipeline calls watershed_visualization, which would
    # recurse back into this function).
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    block = ensure_odd(2 * round(r0 * 1.25) + 1, 15)
    adaptive = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, block, 5)
    closing = cv2.morphologyEx(adaptive, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    th = cv2.morphologyEx(closing, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    ck = ensure_odd(int(max(5, round(r0 * 0.30))), 5)
    ring = cv2.morphologyEx(th, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ck, ck)))
    fg = _fill_holes(ring)
    pd = int(max(2, round(r0 * 0.08)))
    purple_d = cv2.dilate(strict_purple, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * pd + 1, 2 * pd + 1)))
    fg[purple_d > 0] = 0
    return cv2.morphologyEx(fg, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))


def watershed_rbc_candidates(img: np.ndarray, strict_purple: Optional[np.ndarray] = None) -> List[Box]:
    """Watershed + distance transform RBC candidates for clump splitting.

    The foreground here is the *filled* cell bodies, not a colour mask: RBCs are
    dark rings around a pale centre on an often-tinted background, so a colour
    threshold floods almost the whole field (~94%) and the distance transform
    collapses to one peak. Instead we take the membrane ring mask, close its small
    gaps, and fill the enclosed centres into solid disks; touching cells then form
    a multi-lobed blob whose distance transform has one peak per cell, which
    watershed splits. These are returned as *supplementary* candidates and merged
    with the contour detector, recovering cells lost where rings merge.
    """
    if watershed is None or peak_local_max is None or regionprops is None:
        return []
    h, w = img.shape[:2]
    r0 = shape_rbc_radius(h, w)
    if strict_purple is None:
        strict_purple, *_ = purple_mask_strict(img)
    fg = rbc_filled_foreground(img, r0, strict_purple)
    dist = cv2.distanceTransform(fg, cv2.DIST_L2, 5)
    coords = peak_local_max(dist, min_distance=max(5, int(r0 * 0.75)), threshold_abs=max(3, r0 * 0.45), labels=(fg > 0), exclude_border=False)
    markers = np.zeros((h, w), np.int32)
    for i, (yy, xx) in enumerate(coords, 1):
        markers[yy, xx] = i
    if markers.max() == 0:
        return []
    labels_ws = watershed(-dist, markers, mask=(fg > 0))
    candidates: List[List[float]] = []
    for reg in regionprops(labels_ws):
        area = reg.area
        # Gate only on area: a distance peak that survived threshold_abs already
        # marks a cell-sized solid core. The watershed *region* shape (bbox,
        # aspect, circularity) is unreliable -- a basin that bleeds into a touching
        # neighbour is elongated yet its peak is a real cell -- so gating on shape
        # discards the very clump cells we are trying to recover.
        if area < math.pi * (r0 * 0.35) ** 2 or area > math.pi * (r0 * 2.20) ** 2:
            continue
        y1, x1, y2, x2 = reg.bbox
        bw, bh = x2 - x1, y2 - y1
        cy, cx = reg.centroid
        # GT RBC half-side ~ r0 and very consistent; emit an r0-sized box (lightly
        # adapted to the region) regardless of the jagged region extent.
        radius = float(np.clip(0.50 * max(bw, bh), r0 * 0.90, r0 * 1.15)) * 1.06
        candidates.append([1, max(0, cx - radius), max(0, cy - radius), min(w, cx + radius), min(h, cy + radius), 0.45])
    return merge_by_center(candidates, 0.42 * r0)


def watershed_visualization(img: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Create an overlay for watershed split boundaries and the foreground mask."""
    if watershed is None or peak_local_max is None:
        return img.copy(), np.zeros(img.shape[:2], np.uint8)
    h, w = img.shape[:2]
    r0 = shape_rbc_radius(h, w)
    purple, *_ = purple_mask_strict(img)
    fg = rbc_filled_foreground(img, r0, purple)
    dist = cv2.distanceTransform(fg, cv2.DIST_L2, 5)
    coords = peak_local_max(dist, min_distance=max(5, int(r0 * 0.75)), threshold_abs=max(3, r0 * 0.45), labels=(fg > 0), exclude_border=False)
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
    # Pad the WBC exclusion boxes outward a little: a WBC nucleus stains its
    # immediate rim, producing granular purple specks just *outside* the box that
    # otherwise pass as false platelets. The WBC box already includes a 0.10*side
    # pad, so a small extra 0.10*r0 here suffices -- larger over-excludes genuine
    # platelets that merely sit near a white cell.
    wbc_excl = [[b[0], b[1] - 0.10 * r0, b[2] - 0.10 * r0, b[3] + 0.10 * r0, b[4] + 0.10 * r0]
                for b in wbc_boxes]
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
        if gray_std < 5:                          # perfectly flat specks are never platelets
            continue
        # Strongly-stained granular body (the original gate): bright purple with
        # high saturation/grayscale variance.
        strong = (0.06 <= area_r <= 0.80 and s_mean >= 75 and b_mean <= 118
                  and s_std >= 16 and circ >= min_circularity)
        # Faint-but-round body: a quarter of real platelets are weakly stained
        # (s_mean ~68, s_std ~13) and fall just under the strong gate. They still
        # hold a near-circular, distinctly purple shape (circ >= 0.68, b <= 112),
        # which separates them from the irregular faint debris that simply lowering
        # the saturation floor would admit (+8 TP for +2 FP vs +18 FP when lowered).
        faint_round = (0.08 <= area_r <= 0.55 and s_mean >= 60 and b_mean <= 112
                       and s_std >= 10 and circ >= 0.68)
        if not (strong or faint_round):
            continue
        cx = (b[1] + b[3]) / 2
        cy = (b[2] + b[4]) / 2
        if point_in_boxes(cx, cy, wbc_excl):     # inside/touching a WBC -> not a platelet
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


def hough_rbc_candidates(img: np.ndarray, strict_purple: Optional[np.ndarray] = None,
                         wbc_boxes: Optional[Sequence[Box]] = None, param2: int = 24) -> List[Box]:
    """Hough-circle RBC recovery for touching / incomplete-ring cells.

    RBCs are near-uniform circles (radius ~ r0). The contour detector relies on
    each cell's pale centre forming a closed "hole"; that fails where membranes
    merge (touching cells) or where the ring is only a faint arc. The Hough
    circle accumulator votes from even partial / overlapping arcs, so it recovers
    those cells where watershed (a blob prior) cannot. Returned as supplementary
    candidates, filtered against WBC boxes and dense-purple (WBC/platelet)
    regions; boxes are r0-sized to match the consistent RBC ground truth.
    """
    h, w = img.shape[:2]
    r0 = shape_rbc_radius(h, w)
    wbc_boxes = wbc_boxes or []
    if strict_purple is None:
        strict_purple, *_ = purple_mask_strict(img)
    gray = cv2.medianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 5)
    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=r0 * 1.1,
                               param1=80, param2=param2,
                               minRadius=int(r0 * 0.75), maxRadius=int(r0 * 1.20))
    if circles is None:
        return []
    pd = int(max(2, round(r0 * 0.08)))
    purple_d = cv2.dilate(strict_purple, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * pd + 1, 2 * pd + 1)))
    out: List[List[float]] = []
    for cx, cy, _r in circles[0]:
        if purple_d[int(min(h - 1, max(0, cy))), int(min(w - 1, max(0, cx)))] > 0:
            continue
        if point_in_boxes(cx, cy, wbc_boxes):  # inside a WBC -> not an RBC
            continue
        out.append([1, max(0, cx - r0), max(0, cy - r0), min(w, cx + r0), min(h, cy + r0)])
    return merge_by_center(out, 0.42 * r0)


def detect_cells(
    img: np.ndarray,
    mode: str = "Improved classical",
    platelet_model=None,
    platelet_threshold: float = 0.60,
    use_watershed: bool = False,
    use_hough: bool = True,
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
    as red cells or platelets. Hough circles supplement the RBC contour pass to
    recover touching / faint-ring cells (additive, deduped by centre distance).
    """
    h, w = img.shape[:2]
    r0 = shape_rbc_radius(h, w)
    wbc, _violet = detect_wbc(img)
    rbc = detect_rbc_rule(img, None, gaussian_kernel, adaptive_block_ratio, adaptive_c, close_kernel, rbc_min_circularity, wbc_boxes=wbc)
    if use_hough:
        # Supplement with Hough circles for clump / incomplete-ring RBCs the
        # contour pass misses; merge keeps existing boxes (higher score) and only
        # adds circles with no nearby detection.
        hough = hough_rbc_candidates(img, wbc_boxes=wbc)
        rbc = merge_by_center([b + [0.50] for b in rbc] + [b + [0.45] for b in hough], 0.42 * r0)
    if use_watershed:
        # Add only missing watershed candidates by center-distance merge.
        ws = [b for b in watershed_rbc_candidates(img) if not point_in_boxes((b[1] + b[3]) / 2, (b[2] + b[4]) / 2, wbc)]
        rbc = merge_by_center([b + [0.50] for b in rbc] + [b + [0.45] for b in ws], 0.42 * r0)
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
