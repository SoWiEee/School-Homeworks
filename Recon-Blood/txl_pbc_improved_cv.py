"""
Improved classical/non-deep-learning detector for TXL-PBC blood smear images.

Classes:
  0 WBC, 1 RBC, 2 Platelets

Main ideas:
  - WBC: violet/purple stain segmentation + cluster rules.
  - RBC: adaptive-threshold contour detector. A watershed helper is included for
    clump inspection/conservative supplementation, but the default test metrics
    use the more stable adaptive contour branch for RBC counting.
  - Platelets: loose purple candidate extraction + handcrafted component/context
    features + ExtraTreesClassifier. ExtraTrees is classical ML, not deep learning.

Evaluation:
  A prediction is counted as TP when its center is inside a same-class GT box,
  with 15% box-margin tolerance, and one-to-one greedy matching.
"""
from __future__ import annotations

import argparse
import csv
import glob
import math
import os
import pickle
from collections import defaultdict
from typing import Dict, List, Tuple

import cv2
cv2.setNumThreads(1)
import numpy as np

try:
    from skimage.feature import peak_local_max
    from skimage.measure import regionprops
    from skimage.segmentation import watershed
except Exception:  # watershed helper is optional for default evaluation
    peak_local_max = None
    regionprops = None
    watershed = None

Box = List[float]  # [class, x1, y1, x2, y2]
CLASS_NAMES = {0: "WBC", 1: "RBC", 2: "Platelets"}


def shape_rbc_radius(h: int, w: int) -> float:
    """Approximate RBC radius from image resolution, without looking at labels."""
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


def load_yolo_gt(img_path: str, dataset_root: str) -> List[Box]:
    img = cv2.imread(img_path)
    if img is None:
        raise FileNotFoundError(img_path)
    h, w = img.shape[:2]
    split = os.path.basename(os.path.dirname(img_path))
    label_path = os.path.join(dataset_root, "labels", split, os.path.basename(img_path).replace(".png", ".txt"))
    boxes: List[Box] = []
    with open(label_path, "r") as f:
        for line in f:
            if not line.strip():
                continue
            c, xc, yc, bw, bh = map(float, line.split())
            boxes.append([int(c), (xc - bw / 2) * w, (yc - bh / 2) * h, (xc + bw / 2) * w, (yc + bh / 2) * h])
    return boxes


def center_in(pred: Box, gt: Box, margin: float = 0.15) -> bool:
    cx = (pred[1] + pred[3]) / 2
    cy = (pred[2] + pred[4]) / 2
    gw = gt[3] - gt[1]
    gh = gt[4] - gt[2]
    return gt[1] - margin * gw <= cx <= gt[3] + margin * gw and gt[2] - margin * gh <= cy <= gt[4] + margin * gh


def eval_predictions(preds: List[Box], gts: List[Box]) -> Dict[int, Tuple[int, int, int, float, float, float]]:
    out: Dict[int, Tuple[int, int, int, float, float, float]] = {}
    for cls in (0, 1, 2):
        ps = [p for p in preds if p[0] == cls]
        gs = [g for g in gts if g[0] == cls]
        matched = set()
        tp = 0
        for p in ps:
            pcx = (p[1] + p[3]) / 2
            pcy = (p[2] + p[4]) / 2
            best_i = None
            best_dist = float("inf")
            for i, g in enumerate(gs):
                if i in matched or not center_in(p, g):
                    continue
                gcx = (g[1] + g[3]) / 2
                gcy = (g[2] + g[4]) / 2
                dist = (pcx - gcx) ** 2 + (pcy - gcy) ** 2
                if dist < best_dist:
                    best_i = i
                    best_dist = dist
            if best_i is not None:
                matched.add(best_i)
                tp += 1
        fp = len(ps) - tp
        fn = len(gs) - tp
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        out[cls] = (tp, fp, fn, precision, recall, f1)
    return out


def merge_by_center(boxes: List[List[float]], min_dist: float) -> List[Box]:
    if not boxes:
        return []
    # If a score is present at index 5, keep the higher-score box first.
    if len(boxes[0]) > 5:
        boxes = sorted(boxes, key=lambda b: b[5], reverse=True)
    keep: List[Box] = []
    centers = []
    for b in boxes:
        cx = (b[1] + b[3]) / 2
        cy = (b[2] + b[4]) / 2
        if all(((cx - x0) ** 2 + (cy - y0) ** 2) ** 0.5 > min_dist for x0, y0 in centers):
            keep.append(b[:5])
            centers.append((cx, cy))
    return keep


def purple_mask_strict(img: np.ndarray):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    H, S, V = cv2.split(hsv)
    L, A, B = cv2.split(lab)
    purple = (((S > 80) & (V < 210) & (A > 145) & (B < 125)) |
              ((S > 70) & (V < 185) & (A > 140) & (B < 130) & (H > 110) & (H < 175))).astype(np.uint8) * 255
    purple = cv2.medianBlur(purple, 3)
    purple = cv2.morphologyEx(purple, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    return purple, H, S, V, L, A, B


def purple_mask_loose(img: np.ndarray):
    """Looser platelet candidate mask. It is intentionally high-recall."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    H, S, V = cv2.split(hsv)
    L, A, B = cv2.split(lab)
    purple = (((S > 55) & (V < 230) & (A > 136) & (B < 145) & (H > 105) & (H < 178)) |
              ((S > 45) & (V < 200) & (A > 132) & (B < 150) & (H > 115) & (H < 178))).astype(np.uint8) * 255
    purple = cv2.medianBlur(purple, 3)
    purple = cv2.morphologyEx(purple, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    return purple, H, S, V, L, A, B


def detect_wbc(img: np.ndarray) -> Tuple[List[Box], np.ndarray]:
    h, w = img.shape[:2]
    r0 = shape_rbc_radius(h, w)
    purple, H, S, V, L, A, B = purple_mask_strict(img)

    # Merge fragmented nuclei first, then classify the merged violet cluster.
    rad = int(max(5, round(r0 * 0.32)))
    cluster = cv2.dilate(purple, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rad + 1, 2 * rad + 1)))
    ncl, labcl, _, _ = cv2.connectedComponentsWithStats(cluster, 8)
    boxes: List[List[float]] = []
    for ci in range(1, ncl):
        region = (labcl == ci) & (purple > 0)
        original_area = int(region.sum())
        if original_area < max(90, 0.25 * r0 * r0):
            continue
        ys, xs = np.where(region)
        if len(xs) == 0:
            continue
        x1, x2 = int(xs.min()), int(xs.max() + 1)
        y1, y2 = int(ys.min()), int(ys.max() + 1)
        bw, bh = x2 - x1, y2 - y1
        mean_s = float(S[region].mean())
        mean_b = float(B[region].mean())
        mean_h = float(H[region].mean())
        large_geom = (bw > 1.05 * r0 and bh > 0.75 * r0) or (bw > 0.75 * r0 and bh > 1.05 * r0)
        leuk_color = (mean_b < 116 and mean_h < 160) or (mean_s > 108 and mean_b < 120)
        if large_geom and leuk_color:
            pad = int(0.22 * max(bw, bh) + 0.22 * r0)
            score = original_area / (r0 * r0)
            boxes.append([0, max(0, x1 - pad), max(0, y1 - pad), min(w, x2 + pad), min(h, y2 + pad), score])
    return merge_by_center(boxes, 0.90 * r0), purple


def detect_rbc_adaptive(img: np.ndarray, strict_purple: np.ndarray | None = None) -> List[Box]:
    h, w = img.shape[:2]
    r0 = shape_rbc_radius(h, w)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    block_size = int(max(15, 2 * round(r0 * 1.25) + 1))
    th = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, block_size, 5)
    k = max(3, int(round(r0 * 0.03)) * 2 + 1)
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    th = cv2.morphologyEx(th, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))

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
        if circularity < 0.08:
            continue
        moments = cv2.moments(cnt)
        cx, cy = x + bw / 2, y + bh / 2
        if moments["m00"]:
            cx = moments["m10"] / moments["m00"]
            cy = moments["m01"] / moments["m00"]
        if purple_d[int(min(h - 1, max(0, cy))), int(min(w - 1, max(0, cx)))] > 0:
            continue
        radius = float(np.clip(0.5 * max(bw, bh), r0 * 0.47, r0 * 1.35))
        score = circularity - 0.08 * abs(radius - r0) / r0
        candidates.append([1, max(0, cx - radius), max(0, cy - radius), min(w, cx + radius), min(h, cy + radius), score])
    return merge_by_center(candidates, 0.43 * r0)


def detect_rbc_watershed_helper(img: np.ndarray, strict_purple: np.ndarray | None = None) -> List[Box]:
    """
    Watershed helper for RBC clump inspection. On this dataset, the default
    counter keeps adaptive contours because pure watershed over-splits many cells.
    """
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
    ck = int(max(5, round(r0 * 0.18)))
    if ck % 2 == 0:
        ck += 1
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


def extract_platelet_components(img: np.ndarray) -> Tuple[np.ndarray, List[Box]]:
    h, w = img.shape[:2]
    r0 = shape_rbc_radius(h, w)
    mask, H, S, V, L, A, B = purple_mask_loose(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    n, labels, stats, cent = cv2.connectedComponentsWithStats(mask, 8)
    feats = []
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
        crop_label = labels[y:y + bh, x:x + bw]
        pix = crop_label == i
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


def predict_without_platelets(img_path: str) -> Tuple[List[Box], np.ndarray]:
    img = cv2.imread(img_path)
    if img is None:
        raise FileNotFoundError(img_path)
    wbc_boxes, strict_purple = detect_wbc(img)
    rbc_boxes = detect_rbc_adaptive(img, strict_purple)
    return wbc_boxes + rbc_boxes, img


def evaluate(dataset_root: str, split: str, platelet_model_path: str, platelet_threshold: float = 0.60) -> Dict[int, Tuple[int, int, int, float, float, float]]:
    with open(platelet_model_path, "rb") as f:
        platelet_model = pickle.load(f)

    paths = sorted(glob.glob(os.path.join(dataset_root, "images", split, "*.png")))
    base_preds: Dict[str, List[Box]] = {}
    platelet_features = []
    platelet_meta = []

    for path in paths:
        base, img = predict_without_platelets(path)
        base_preds[path] = base
        features, boxes = extract_platelet_components(img)
        if len(boxes):
            platelet_features.append(features)
            platelet_meta.extend((path, box) for box in boxes)

    platelet_by_path: Dict[str, List[List[float]]] = defaultdict(list)
    if platelet_features:
        X = np.vstack(platelet_features)
        probs = platelet_model.predict_proba(X)[:, 1]
        for (path, box), prob in zip(platelet_meta, probs):
            if prob >= platelet_threshold:
                platelet_by_path[path].append(box + [float(prob)])

    total = {0: [0, 0, 0], 1: [0, 0, 0], 2: [0, 0, 0]}
    for path in paths:
        img = cv2.imread(path)
        h, w = img.shape[:2]
        r0 = shape_rbc_radius(h, w)
        platelets = merge_by_center(platelet_by_path.get(path, []), 0.42 * r0)
        preds = base_preds[path] + platelets
        ev = eval_predictions(preds, load_yolo_gt(path, dataset_root))
        for c in total:
            for i in range(3):
                total[c][i] += ev[c][i]

    result: Dict[int, Tuple[int, int, int, float, float, float]] = {}
    for c, (tp, fp, fn) in total.items():
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * p * r / (p + r) if p + r else 0.0
        result[c] = (tp, fp, fn, p, r, f1)
    return result


def write_metrics_csv(path: str, result: Dict[int, Tuple[int, int, int, float, float, float]]) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["class", "tp", "fp", "fn", "precision", "recall", "f1"])
        micro_tp = micro_fp = micro_fn = 0
        for c in (0, 1, 2):
            tp, fp, fn, p, r, f1 = result[c]
            micro_tp += tp
            micro_fp += fp
            micro_fn += fn
            writer.writerow([CLASS_NAMES[c], tp, fp, fn, f"{p:.4f}", f"{r:.4f}", f"{f1:.4f}"])
        p = micro_tp / (micro_tp + micro_fp) if micro_tp + micro_fp else 0.0
        r = micro_tp / (micro_tp + micro_fn) if micro_tp + micro_fn else 0.0
        f1 = 2 * p * r / (p + r) if p + r else 0.0
        writer.writerow(["micro", micro_tp, micro_fp, micro_fn, f"{p:.4f}", f"{r:.4f}", f"{f1:.4f}"])


def print_metrics(result: Dict[int, Tuple[int, int, int, float, float, float]]) -> None:
    print("class,tp,fp,fn,precision,recall,f1")
    micro_tp = micro_fp = micro_fn = 0
    for c in (0, 1, 2):
        tp, fp, fn, p, r, f1 = result[c]
        micro_tp += tp
        micro_fp += fp
        micro_fn += fn
        print(f"{CLASS_NAMES[c]},{tp},{fp},{fn},{p:.4f},{r:.4f},{f1:.4f}")
    p = micro_tp / (micro_tp + micro_fp) if micro_tp + micro_fp else 0.0
    r = micro_tp / (micro_tp + micro_fn) if micro_tp + micro_fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    print(f"micro,{micro_tp},{micro_fp},{micro_fn},{p:.4f},{r:.4f},{f1:.4f}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="/mnt/data/TXL-PBC_Dataset/TXL-PBC")
    parser.add_argument("--split", default="test", choices=["train", "val", "test"])
    parser.add_argument("--platelet-model", default="/mnt/data/et_platelet_model.pkl")
    parser.add_argument("--platelet-threshold", type=float, default=0.60)
    parser.add_argument("--csv", default="")
    args = parser.parse_args()

    result = evaluate(args.root, args.split, args.platelet_model, args.platelet_threshold)
    print_metrics(result)
    if args.csv:
        write_metrics_csv(args.csv, result)


if __name__ == "__main__":
    main()
