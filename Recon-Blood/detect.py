"""
Blood cell detection using classical image processing.
Classes: 0=WBC, 1=RBC, 2=Platelet  |  Image: 575×575 px
"""

import cv2
import numpy as np
import glob
import os

# ── WBC ───────────────────────────────────────────────────────────────────────
WBC_GRAY_THRESH = 130
WBC_CLOSE_K     = 23
WBC_OPEN_K      = 9
WBC_MIN_AREA    = 9500
WBC_PAD         = 65

# ── RBC (Hough Circles) ───────────────────────────────────────────────────────
RBC_MIN_DIST = 38
RBC_PARAM1   = 50
RBC_PARAM2   = 12
RBC_MIN_R    = 28
RBC_MAX_R    = 78

# ── PLT ───────────────────────────────────────────────────────────────────────
PLT_H_LO     = 112
PLT_H_HI     = 162
PLT_S_MIN    = 38
PLT_V_HI     = 210
PLT_MIN_AREA = 400
PLT_MAX_AREA = 3000

# ── Evaluation ────────────────────────────────────────────────────────────────
IOU_THRESH = 0.5
IMG_SIZE   = 575


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
    """
    Returns (wbc_boxes, rbc_boxes, plt_boxes, debug_img).
    Each *_boxes is a list of [x1, y1, x2, y2] pixel coords.

    Step 1: WBC  — gray threshold + purple HSV → large contours
    Step 2: RBC  — Hough Circle Transform (counting)
              +  Hough-seeded Watershed (boundary visualization)
    Step 3: PLT  — purple HSV mask
    """
    h, w = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    hsv  = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    # ── Step 1: WBC ────────────────────────────────────────────────────
    g_blur = cv2.GaussianBlur(gray, (11, 11), 2)
    _, dark = cv2.threshold(g_blur, WBC_GRAY_THRESH, 255, cv2.THRESH_BINARY_INV)
    purple = cv2.inRange(hsv, (100, 25, 20), (168, 255, 200))
    dark = cv2.bitwise_and(dark, purple)
    dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE,
                            np.ones((WBC_CLOSE_K, WBC_CLOSE_K), np.uint8))
    dark = cv2.morphologyEx(dark, cv2.MORPH_OPEN,
                            np.ones((WBC_OPEN_K,  WBC_OPEN_K),  np.uint8))

    wbc_cnts, _ = cv2.findContours(dark, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    wbc_cnts = [c for c in wbc_cnts if cv2.contourArea(c) >= WBC_MIN_AREA]

    wbc_excl = np.zeros((h, w), np.uint8)
    for cnt in wbc_cnts:
        x, y, bw, bh = cv2.boundingRect(cnt)
        cv2.rectangle(wbc_excl,
                      (max(0, x - WBC_PAD),      max(0, y - WBC_PAD)),
                      (min(w, x + bw + WBC_PAD), min(h, y + bh + WBC_PAD)),
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
            if wbc_excl[cy_c, cx_c] == 0:
                rbc_centers.append((int(cx), int(cy), int(r)))

    # ── Step 2b: Hough-seeded Watershed boundary visualization ─────────
    ws_markers = _hough_seeded_watershed(img_bgr, rbc_centers, h, w)

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
    wbc_boxes = []
    for cnt in wbc_cnts:
        x, y, bw, bh = cv2.boundingRect(cnt)
        wbc_boxes.append([x, y, x + bw, y + bh])

    rbc_boxes = []
    for (cx, cy, r) in rbc_centers:
        rbc_boxes.append([max(0, cx - r), max(0, cy - r),
                          min(w, cx + r), min(h, cy + r)])

    plt_boxes = []
    for cnt in plt_dets:
        x, y, bw, bh = cv2.boundingRect(cnt)
        plt_boxes.append([x, y, x + bw, y + bh])

    # ── Debug visualization ────────────────────────────────────────────
    debug = img_bgr.copy()
    boundary = (ws_markers == -1).astype(np.uint8)
    boundary = cv2.dilate(boundary, np.ones((2, 2), np.uint8), iterations=1)
    debug[boundary > 0] = [0, 220, 220]  # Watershed boundaries in yellow (thickened)

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
            x1 = round((cx - bw / 2) * img_w)
            y1 = round((cy - bh / 2) * img_h)
            x2 = round((cx + bw / 2) * img_w)
            y2 = round((cy + bh / 2) * img_h)
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


def draw_gt_pred(img_bgr, gt_by_cls, pred_by_cls):
    """Draw GT (thin) and predicted (thick) bounding boxes on image."""
    GT_COLORS   = {0: (0, 230, 0),   1: (230, 180, 0), 2: (200, 0, 200)}
    PRED_COLORS = {0: (0, 200, 0),   1: (0, 0, 220),   2: (220, 0, 0)}
    NAMES = {0: 'WBC', 1: 'RBC', 2: 'PLT'}
    vis = img_bgr.copy()
    for cls, boxes in gt_by_cls.items():
        c = GT_COLORS[cls]
        for box in boxes:
            x1, y1, x2, y2 = box
            cv2.rectangle(vis, (x1, y1), (x2, y2), c, 1)
    for cls, boxes in pred_by_cls.items():
        c = PRED_COLORS[cls]
        name = NAMES[cls]
        for box in boxes:
            x1, y1, x2, y2 = box
            cv2.rectangle(vis, (x1, y1), (x2, y2), c, 2)
            cv2.putText(vis, name, (x1, max(0, y1 - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, c, 1)
    return vis


def evaluate(split="test", iou_thresh=IOU_THRESH, verbose=False, save_vis_dir=None):
    img_dir   = f"TXL-PBC_Dataset/TXL-PBC/images/{split}"
    label_dir = f"TXL-PBC_Dataset/TXL-PBC/labels/{split}"
    img_files = sorted(glob.glob(f"{img_dir}/*.png"))

    totals = {cls: {"tp": 0, "fp": 0, "fn": 0} for cls in [0, 1, 2]}

    for img_path in img_files:
        stem = os.path.splitext(os.path.basename(img_path))[0]
        lbl  = f"{label_dir}/{stem}.txt"
        img  = cv2.imread(img_path)
        gt   = load_gt(lbl)
        wbc_boxes, rbc_boxes, plt_boxes, debug = detect_cells(img)
        pred = {0: wbc_boxes, 1: rbc_boxes, 2: plt_boxes}

        for cls in [0, 1, 2]:
            tp, fp, fn = match_detections(gt[cls], pred[cls], iou_thresh)
            totals[cls]["tp"] += tp
            totals[cls]["fp"] += fp
            totals[cls]["fn"] += fn

        if verbose:
            print(f"  {stem[:20]}  "
                  f"WBC GT={len(gt[0])} P={len(wbc_boxes)}  "
                  f"RBC GT={len(gt[1])} P={len(rbc_boxes)}  "
                  f"PLT GT={len(gt[2])} P={len(plt_boxes)}")

        if save_vis_dir:
            os.makedirs(save_vis_dir, exist_ok=True)
            vis = draw_gt_pred(img, gt, pred)
            cv2.imwrite(f"{save_vis_dir}/{stem}.png", vis)

    names = {0: "WBC", 1: "RBC", 2: "PLT"}
    print(f"\n{'='*64}")
    print(f"  Split: {split}  ({len(img_files)} images)  IoU≥{iou_thresh}")
    print(f"{'='*64}")
    print(f"{'Cell':<6} {'TP':>6} {'FP':>6} {'FN':>6} {'Precision':>10} {'Recall':>8}")
    print(f"{'-'*64}")
    results = {}
    for cls in [0, 1, 2]:
        tp   = totals[cls]["tp"]
        fp   = totals[cls]["fp"]
        fn   = totals[cls]["fn"]
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec  = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        name = names[cls]
        results[name] = {"tp": tp, "fp": fp, "fn": fn,
                         "precision": prec, "recall": rec}
        print(f"{name:<6} {tp:>6} {fp:>6} {fn:>6} {prec:>10.1%} {rec:>8.1%}")
    print(f"{'='*64}")
    return results


if __name__ == "__main__":
    evaluate("test")
