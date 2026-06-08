"""
Blood cell detection using classical image processing.
Classes: 0=WBC, 1=RBC, 2=Platelet  |  Image: 575×575 px
"""

import argparse
import csv
import cv2
import numpy as np
import glob
import os

# ── WBC ───────────────────────────────────────────────────────────────────────
WBC_GRAY_THRESH = 105
WBC_CLOSE_K     = 23
WBC_MIN_AREA    = 1000
WBC_PAD         = 20
WBC_BOX_PAD     = 35
WBC_MAX_DETECTIONS = 1

# ── RBC (Hough Circles) ───────────────────────────────────────────────────────
RBC_MIN_DIST = 38
RBC_PARAM1   = 50
RBC_PARAM2   = 15
RBC_MIN_R    = 28
RBC_MAX_R    = 78
RBC_BOX_PAD  = 0
RBC_AREA_MIN = 2500
RBC_AREA_MAX = 15500
RBC_CIRCULARITY_MIN = 0.82
RBC_USE_COLOR_FILTER = False
RBC_FILTER_R_MAX = 70
RBC_FILTER_GRAY_STD_MAX = 32
RBC_FILTER_S_MED_MAX = 110
RBC_FILTER_V_MED_MAX = 235

# ── PLT ───────────────────────────────────────────────────────────────────────
PLT_H_LO     = 112
PLT_H_HI     = 162
PLT_S_MIN    = 38
PLT_V_HI     = 210
PLT_MIN_AREA = 400
PLT_MAX_AREA = 0
PLT_BOX_PAD  = 18

# ── Evaluation ────────────────────────────────────────────────────────────────
IOU_THRESH = 0.3
DRAW_WATERSHED_BOUNDARIES = False
IMG_SIZE   = 575


def _pad_box(box, pad, w, h):
    x1, y1, x2, y2 = box
    return [
        max(0, x1 - pad),
        max(0, y1 - pad),
        min(w, x2 + pad),
        min(h, y2 + pad),
    ]


def _box_area(box):
    return max(0, box[2] - box[0]) * max(0, box[3] - box[1])


def _wbc_seeded_watershed(img_bgr, dark_mask, h, w):
    """
    WBC segmentation via per-component Distance Transform + Watershed.

    Per-component thresholding ensures every blob (large or small) gets its
    own seed, so a single WBC with a complex/lobed nucleus stays as 1 detection
    while two touching WBCs (merged by morphClose into 1 blob) produce 2 seeds
    from 2 separate DT peaks and get split by Watershed.

    Returns (wbc_boxes, ws_markers).  ws_markers == -1 → boundary pixel.
    """
    sure_fg = np.zeros((h, w), np.uint8)
    n_blobs, blob_labels = cv2.connectedComponents(dark_mask)
    for lbl in range(1, n_blobs):
        blob_mask = ((blob_labels == lbl) * 255).astype(np.uint8)
        if np.sum(blob_mask > 0) < 2000:   # skip tiny noise blobs
            continue
        local_dist = cv2.distanceTransform(blob_mask, cv2.DIST_L2, 5)
        local_max  = local_dist.max()
        if local_max == 0:
            continue
        _, fg = cv2.threshold(local_dist, 0.5 * local_max, 255, cv2.THRESH_BINARY)
        sure_fg = cv2.bitwise_or(sure_fg, fg.astype(np.uint8))

    sure_bg = cv2.dilate(dark_mask, np.ones((5, 5), np.uint8), iterations=2)
    unknown = cv2.subtract(sure_bg, sure_fg)

    _, markers = cv2.connectedComponents(sure_fg)
    markers = markers + 1          # background → label 1
    markers[unknown == 255] = 0    # unknown → 0

    markers = cv2.watershed(img_bgr.copy(), markers)

    boxes = []
    for label in np.unique(markers):
        if label <= 1:             # skip background (1) and boundary (-1)
            continue
        region = (markers == label).astype(np.uint8) * 255
        cnts, _ = cv2.findContours(region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in cnts:
            if cv2.contourArea(cnt) >= WBC_MIN_AREA:
                x, y, bw, bh = cv2.boundingRect(cnt)
                boxes.append([x, y, x + bw, y + bh])
    return boxes, markers


def _hough_seeded_watershed(img_bgr, rbc_centers, h, w):
    """
    Hough-seeded Watershed: draws Hough circles as cell regions, dilates to connect
    adjacent circles, then lets Watershed find boundaries between touching RBCs.
    Returns ws_markers (-1 = boundary pixels).
    """
    cell_mask = np.zeros((h, w), np.uint8)
    for (cx, cy, r) in rbc_centers:
        cv2.circle(cell_mask, (cx, cy), r, 255, -1)
    cell_union = cv2.dilate(cell_mask, np.ones((7, 7), np.uint8), iterations=1)

    markers = np.zeros((h, w), np.int32)
    markers[cell_union == 0] = 1   # sure background → label 1
    for i, (cx, cy, r) in enumerate(rbc_centers):
        seed_r = max(3, r // 4)
        cx_c = int(np.clip(cx, 0, w - 1))
        cy_c = int(np.clip(cy, 0, h - 1))
        cv2.circle(markers, (cx_c, cy_c), seed_r, i + 2, -1)

    markers = cv2.watershed(img_bgr.copy(), markers.copy())
    return markers


def detect_cells(img_bgr):
    """Return detected WBC/RBC/PLT boxes and a debug image.

    The primary classification rule is area + circularity:
    WBC uses large purple connected components, RBC uses circular Hough
    candidates filtered by circle area, and PLT uses a conservative small
    purple-area rule.
    """
    h, w = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    hsv  = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    # ── Step 1: WBC (Watershed segmentation) ──────────────────────────
    g_blur = cv2.GaussianBlur(gray, (11, 11), 2)
    _, dark = cv2.threshold(g_blur, WBC_GRAY_THRESH, 255, cv2.THRESH_BINARY_INV)
    purple = cv2.inRange(hsv, (100, 25, 20), (168, 255, 200))
    dark = cv2.bitwise_and(dark, purple)
    dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE,
                            np.ones((WBC_CLOSE_K, WBC_CLOSE_K), np.uint8))
    # morphOpen removed: it was fragmenting multi-lobed WBC nuclei into multiple
    # blobs. Per-component DT Watershed handles noise via the area filter instead.

    wbc_raw_boxes, wbc_ws_markers = _wbc_seeded_watershed(img_bgr, dark, h, w)
    wbc_boxes = [_pad_box(box, WBC_BOX_PAD, w, h) for box in wbc_raw_boxes]
    wbc_boxes = sorted(wbc_boxes, key=_box_area, reverse=True)[:WBC_MAX_DETECTIONS]

    wbc_excl = np.zeros((h, w), np.uint8)
    for box in wbc_boxes:
        x1, y1, x2, y2 = box
        cv2.rectangle(wbc_excl,
                      (max(0, x1 - WBC_PAD), max(0, y1 - WBC_PAD)),
                      (min(w, x2 + WBC_PAD), min(h, y2 + WBC_PAD)),
                      255, -1)

    # ── Step 2a: RBC counting via Hough Circles ────────────────────────
    blur5 = cv2.GaussianBlur(gray, (5, 5), 1)
    circles = cv2.HoughCircles(
        blur5, cv2.HOUGH_GRADIENT, dp=1,
        minDist=RBC_MIN_DIST, param1=RBC_PARAM1, param2=RBC_PARAM2,
        minRadius=RBC_MIN_R, maxRadius=RBC_MAX_R
    )
    rbc_centers = []
    if circles is not None:
        for (cx, cy, r) in np.round(circles[0]).astype(int):
            cy_c = int(np.clip(cy, 0, h - 1))
            cx_c = int(np.clip(cx, 0, w - 1))
            x1 = max(0, int(cx - r))
            y1 = max(0, int(cy - r))
            x2 = min(w, int(cx + r))
            y2 = min(h, int(cy + r))
            area = np.pi * (r ** 2)
            circularity = 1.0  # Hough circles are circular candidates by construction.
            is_rbc_like = (
                RBC_AREA_MIN <= area <= RBC_AREA_MAX and
                circularity >= RBC_CIRCULARITY_MIN
            )
            if RBC_USE_COLOR_FILTER:
                roi_gray = gray[y1:y2, x1:x2]
                roi_hsv = hsv[y1:y2, x1:x2]
                if roi_gray.size == 0:
                    continue
                gray_std = float(roi_gray.std())
                s_med = float(np.median(roi_hsv[:, :, 1]))
                v_med = float(np.median(roi_hsv[:, :, 2]))
                is_rbc_like = is_rbc_like and (
                    r <= RBC_FILTER_R_MAX and
                    gray_std <= RBC_FILTER_GRAY_STD_MAX and
                    s_med <= RBC_FILTER_S_MED_MAX and
                    v_med <= RBC_FILTER_V_MED_MAX
                )
            if wbc_excl[cy_c, cx_c] == 0 and is_rbc_like:
                rbc_centers.append((int(cx), int(cy), int(r)))

    # ── Step 3: PLT ────────────────────────────────────────────────────
    rbc_excl = np.zeros((h, w), np.uint8)
    for (cx, cy, r) in rbc_centers:
        cv2.circle(rbc_excl, (cx, cy), r + 10, 255, -1)

    all_excl = cv2.bitwise_or(wbc_excl, rbc_excl)
    purp_mask = cv2.inRange(hsv, (PLT_H_LO, PLT_S_MIN, 30), (PLT_H_HI, 255, PLT_V_HI))
    purp_mask = cv2.bitwise_and(purp_mask, cv2.bitwise_not(all_excl))
    purp_mask = cv2.morphologyEx(purp_mask, cv2.MORPH_OPEN,  np.ones((2, 2), np.uint8))
    purp_mask = cv2.morphologyEx(purp_mask, cv2.MORPH_CLOSE, np.ones((4, 4), np.uint8))

    plt_cnts_all, _ = cv2.findContours(purp_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    plt_dets = [c for c in plt_cnts_all
                if PLT_MIN_AREA <= cv2.contourArea(c) <= PLT_MAX_AREA]

    # ── Collect bounding boxes ─────────────────────────────────────────
    rbc_boxes = []
    for (cx, cy, r) in rbc_centers:
        rbc_boxes.append(_pad_box([max(0, cx - r), max(0, cy - r),
                                   min(w, cx + r), min(h, cy + r)],
                                  RBC_BOX_PAD, w, h))

    plt_boxes = []
    for cnt in plt_dets:
        x, y, bw, bh = cv2.boundingRect(cnt)
        plt_boxes.append(_pad_box([x, y, x + bw, y + bh], PLT_BOX_PAD, w, h))

    # ── Debug visualization ────────────────────────────────────────────
    debug = img_bgr.copy()

    if DRAW_WATERSHED_BOUNDARIES:
        wbc_boundary = (wbc_ws_markers == -1).astype(np.uint8)
        wbc_boundary = cv2.dilate(wbc_boundary, np.ones((2, 2), np.uint8), iterations=1)
        debug[wbc_boundary > 0] = [200, 0, 200]

    for box in wbc_boxes:
        x1, y1, x2, y2 = box
        cv2.rectangle(debug, (x1, y1), (x2, y2), (0, 200, 0), 2)
        cv2.putText(debug, "WBC", (x1, max(0, y1 - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1)
    for (cx, cy, r) in rbc_centers:
        cv2.circle(debug, (cx, cy), r, (0, 0, 220), 1)
    for box in plt_boxes:
        x1, y1, x2, y2 = box
        cv2.rectangle(debug, (x1, y1), (x2, y2), (220, 0, 0), 1)

    return wbc_boxes, rbc_boxes, plt_boxes, debug


def load_gt(label_path, img_w=IMG_SIZE, img_h=IMG_SIZE):
    """Parse YOLO format labels. Returns {0: [[x1,y1,x2,y2],...], 1:[...], 2:[...]}"""
    boxes = {0: [], 1: [], 2: []}
    if not os.path.exists(label_path):
        return boxes
    with open(label_path) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            cls = int(parts[0])
            cx, cy, bw, bh = map(float, parts[1:5])
            x1 = int(np.clip(round((cx - bw / 2) * img_w), 0, img_w - 1))
            y1 = int(np.clip(round((cy - bh / 2) * img_h), 0, img_h - 1))
            x2 = int(np.clip(round((cx + bw / 2) * img_w), 0, img_w))
            y2 = int(np.clip(round((cy + bh / 2) * img_h), 0, img_h))
            if cls in boxes:
                boxes[cls].append([x1, y1, x2, y2])
    return boxes


def iou(boxA, boxB):
    x_left   = max(boxA[0], boxB[0])
    y_top    = max(boxA[1], boxB[1])
    x_right  = min(boxA[2], boxB[2])
    y_bottom = min(boxA[3], boxB[3])
    inter = max(0, x_right - x_left) * max(0, y_bottom - y_top)
    if inter == 0:
        return 0.0
    area_a = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    area_b = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    if area_a <= 0 or area_b <= 0:
        return 0.0
    return inter / (area_a + area_b - inter)


def match_detections(gt_boxes, pred_boxes, iou_thresh=IOU_THRESH):
    """Greedy one-to-one IoU matching. Returns (tp, fp, fn)."""
    matched_gt   = set()
    matched_pred = set()
    pairs = []
    for i, gb in enumerate(gt_boxes):
        for j, pb in enumerate(pred_boxes):
            score = iou(gb, pb)
            if score >= iou_thresh:
                pairs.append((score, i, j))
    pairs.sort(reverse=True)
    for _, i, j in pairs:
        if i not in matched_gt and j not in matched_pred:
            matched_gt.add(i)
            matched_pred.add(j)
    tp = len(matched_gt)
    fp = len(pred_boxes) - len(matched_pred)
    fn = len(gt_boxes)   - len(matched_gt)
    return tp, fp, fn


def calc_metrics(tp, fp, fn):
    """Return precision, recall, and F1 from accumulated TP/FP/FN."""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1


def draw_gt_pred(img_bgr, gt_by_cls, pred_by_cls):
    """Draw GT (thin) and predicted (thick) bounding boxes on image."""
    GT_COLORS   = {0: (0, 230, 0),   1: (230, 180, 0), 2: (200, 0, 200)}
    PRED_COLORS = {0: (0, 200, 0),   1: (0, 0, 220),   2: (220, 0, 0)}
    NAMES = {0: 'WBC', 1: 'RBC', 2: 'PLT'}
    vis = img_bgr.copy()
    for cls, boxes in gt_by_cls.items():
        c = GT_COLORS[cls]
        name = NAMES[cls]
        for box in boxes:
            x1, y1, x2, y2 = box
            cv2.rectangle(vis, (x1, y1), (x2, y2), c, 1)
            cv2.putText(vis, f"GT:{name}", (x1, max(0, y1 - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, c, 1)
    for cls, boxes in pred_by_cls.items():
        c = PRED_COLORS[cls]
        name = NAMES[cls]
        for box in boxes:
            x1, y1, x2, y2 = box
            cv2.rectangle(vis, (x1, y1), (x2, y2), c, 2)
            cv2.putText(vis, f"Pred:{name}", (x1, max(0, y1 - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, c, 1)
    return vis


def evaluate(split="test", iou_thresh=IOU_THRESH, verbose=False, save_vis_dir=None,
             dataset_root="TXL-PBC_Dataset/TXL-PBC", csv_path=None, max_images=None):
    img_dir   = os.path.join(dataset_root, "images", split)
    label_dir = os.path.join(dataset_root, "labels", split)
    img_files = sorted(glob.glob(f"{img_dir}/*.png"))
    if max_images is not None:
        img_files = img_files[:max_images]
    if not img_files:
        raise FileNotFoundError(f"No PNG images found in: {img_dir}")

    totals = {cls: {"tp": 0, "fp": 0, "fn": 0} for cls in [0, 1, 2]}
    count_totals = {cls: {"gt": 0, "pred": 0} for cls in [0, 1, 2]}
    rows = []

    for img_path in img_files:
        stem = os.path.splitext(os.path.basename(img_path))[0]
        lbl  = os.path.join(label_dir, f"{stem}.txt")
        img  = cv2.imread(img_path)
        if img is None:
            print(f"Skip unreadable image: {img_path}")
            continue
        h, w = img.shape[:2]
        gt   = load_gt(lbl, w, h)
        wbc_boxes, rbc_boxes, plt_boxes, debug = detect_cells(img)
        pred = {0: wbc_boxes, 1: rbc_boxes, 2: plt_boxes}
        row = {"image": stem}

        for cls in [0, 1, 2]:
            tp, fp, fn = match_detections(gt[cls], pred[cls], iou_thresh)
            totals[cls]["tp"] += tp
            totals[cls]["fp"] += fp
            totals[cls]["fn"] += fn
            count_totals[cls]["gt"] += len(gt[cls])
            count_totals[cls]["pred"] += len(pred[cls])
            precision, recall, f1 = calc_metrics(tp, fp, fn)
            name = {0: "WBC", 1: "RBC", 2: "PLT"}[cls]
            row[f"{name}_gt"] = len(gt[cls])
            row[f"{name}_pred"] = len(pred[cls])
            row[f"{name}_tp"] = tp
            row[f"{name}_fp"] = fp
            row[f"{name}_fn"] = fn
            row[f"{name}_precision"] = precision
            row[f"{name}_recall"] = recall
            row[f"{name}_f1"] = f1
        rows.append(row)

        if verbose:
            print(f"  {stem[:20]}  "
                  f"WBC GT={len(gt[0])} P={len(wbc_boxes)}  "
                  f"RBC GT={len(gt[1])} P={len(rbc_boxes)}  "
                  f"PLT GT={len(gt[2])} P={len(plt_boxes)}")

        if save_vis_dir:
            os.makedirs(save_vis_dir, exist_ok=True)
            vis = draw_gt_pred(img, gt, pred)
            cv2.imwrite(os.path.join(save_vis_dir, f"{stem}.png"), vis)

    if csv_path:
        os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
        fieldnames = ["image"]
        for name in ["WBC", "RBC", "PLT"]:
            fieldnames.extend([
                f"{name}_gt", f"{name}_pred", f"{name}_tp", f"{name}_fp", f"{name}_fn",
                f"{name}_precision", f"{name}_recall", f"{name}_f1",
            ])
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    names = {0: "WBC", 1: "RBC", 2: "PLT"}
    print(f"\n{'='*88}")
    print(f"  Split: {split}  ({len(img_files)} images)  IoU>={iou_thresh}")
    print(f"{'='*88}")
    print(f"{'Cell':<6} {'GT':>6} {'Pred':>6} {'TP':>6} {'FP':>6} {'FN':>6} "
          f"{'Precision':>10} {'Recall':>8} {'F1':>8} {'CntErr':>8}")
    print(f"{'-'*88}")
    results = {}
    for cls in [0, 1, 2]:
        tp   = totals[cls]["tp"]
        fp   = totals[cls]["fp"]
        fn   = totals[cls]["fn"]
        gt_count = count_totals[cls]["gt"]
        pred_count = count_totals[cls]["pred"]
        prec, rec, f1 = calc_metrics(tp, fp, fn)
        count_err = (pred_count - gt_count) / gt_count if gt_count > 0 else 0.0
        name = names[cls]
        results[name] = {"tp": tp, "fp": fp, "fn": fn,
                         "gt": gt_count, "pred": pred_count,
                         "precision": prec, "recall": rec, "f1": f1,
                         "count_error": count_err}
        print(f"{name:<6} {gt_count:>6} {pred_count:>6} {tp:>6} {fp:>6} {fn:>6} "
              f"{prec:>10.1%} {rec:>8.1%} {f1:>8.1%} {count_err:>8.1%}")

    micro_tp = sum(totals[cls]["tp"] for cls in [0, 1, 2])
    micro_fp = sum(totals[cls]["fp"] for cls in [0, 1, 2])
    micro_fn = sum(totals[cls]["fn"] for cls in [0, 1, 2])
    micro_p, micro_r, micro_f1 = calc_metrics(micro_tp, micro_fp, micro_fn)
    macro_p = sum(results[names[cls]]["precision"] for cls in [0, 1, 2]) / 3
    macro_r = sum(results[names[cls]]["recall"] for cls in [0, 1, 2]) / 3
    macro_f1 = sum(results[names[cls]]["f1"] for cls in [0, 1, 2]) / 3
    results["micro_avg"] = {"tp": micro_tp, "fp": micro_fp, "fn": micro_fn,
                            "precision": micro_p, "recall": micro_r, "f1": micro_f1}
    results["macro_avg"] = {"precision": macro_p, "recall": macro_r, "f1": macro_f1}

    print(f"{'-'*88}")
    print(f"{'Micro':<6} {'':>6} {'':>6} {micro_tp:>6} {micro_fp:>6} {micro_fn:>6} "
          f"{micro_p:>10.1%} {micro_r:>8.1%} {micro_f1:>8.1%} {'':>8}")
    print(f"{'Macro':<6} {'':>6} {'':>6} {'':>6} {'':>6} {'':>6} "
          f"{macro_p:>10.1%} {macro_r:>8.1%} {macro_f1:>8.1%} {'':>8}")
    print(f"{'='*88}")
    if csv_path:
        print(f"Per-image metrics saved to: {csv_path}")
    if save_vis_dir:
        print(f"GT/pred visualizations saved to: {save_vis_dir}")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate classical blood cell detection metrics.")
    parser.add_argument("--split", default="test", choices=["train", "val", "test", "all"],
                        help="Dataset split to evaluate.")
    parser.add_argument("--dataset-root", default="TXL-PBC_Dataset/TXL-PBC",
                        help="Path containing images/ and labels/ folders.")
    parser.add_argument("--iou", type=float, default=IOU_THRESH,
                        help="IoU threshold for one-to-one matching.")
    parser.add_argument("--verbose", action="store_true",
                        help="Print per-image detection counts.")
    parser.add_argument("--save-vis-dir", default=None,
                        help="Optional directory for GT/pred overlay images.")
    parser.add_argument("--csv", default=None,
                        help="Optional CSV path for per-image metrics.")
    parser.add_argument("--max-images", type=int, default=None,
                        help="Optional limit for quick calibration runs.")
    args = parser.parse_args()

    if args.split == "all":
        for split_name in ["train", "val", "test"]:
            split_vis_dir = os.path.join(args.save_vis_dir, split_name) if args.save_vis_dir else None
            split_csv = None
            if args.csv:
                base, ext = os.path.splitext(args.csv)
                split_csv = f"{base}_{split_name}{ext or '.csv'}"
            evaluate(split_name, args.iou, args.verbose, split_vis_dir,
                     args.dataset_root, split_csv, args.max_images)
    else:
        evaluate(args.split, args.iou, args.verbose, args.save_vis_dir,
                 args.dataset_root, args.csv, args.max_images)
