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

# ── Watershed (visualization only) ───────────────────────────────────────────
WS_CLOSE_K     = 18
WS_DIST_THRESH = 0.40


def _hough_seeded_watershed(img_bgr, rbc_centers, h, w):
    """
    Hough-seeded Watershed: draws Hough circles as cell regions, dilates to connect
    adjacent circles, then lets Watershed find boundaries between touching RBCs.
    Returns ws_markers (-1 = boundary pixels).
    """
    # Draw filled Hough circles; dilate to connect adjacent cells
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
    Returns (wbc_count, rbc_count, plt_count, debug_img).

    Step 1: WBC  — gray threshold + purple HSV → large contours
    Step 2: RBC  — Hough Circle Transform (counting)
              +  Watershed + Distance Transform (boundary visualization)
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

    # ── Debug visualization ────────────────────────────────────────────
    debug = img_bgr.copy()
    boundary = (ws_markers == -1).astype(np.uint8)
    boundary = cv2.dilate(boundary, np.ones((2, 2), np.uint8), iterations=1)
    debug[boundary > 0] = [0, 220, 220]  # Watershed boundaries in yellow (thickened)
    for cnt in wbc_cnts:
        x, y, bw, bh = cv2.boundingRect(cnt)
        cv2.rectangle(debug, (x, y), (x + bw, y + bh), (0, 200, 0), 2)
        cv2.putText(debug, "WBC", (x, max(0, y - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1)
    for (cx, cy, r) in rbc_centers:
        cv2.circle(debug, (cx, cy), r, (0, 0, 220), 1)
    for cnt in plt_dets:
        x, y, bw, bh = cv2.boundingRect(cnt)
        cv2.rectangle(debug, (x, y), (x + bw, y + bh), (220, 0, 0), 1)

    return len(wbc_cnts), len(rbc_centers), len(plt_dets), debug


def load_gt(label_path):
    wbc = rbc = plt = 0
    if not os.path.exists(label_path):
        return wbc, rbc, plt
    with open(label_path) as f:
        for line in f:
            cls = int(line.split()[0])
            if cls == 0:   wbc += 1
            elif cls == 1: rbc += 1
            elif cls == 2: plt += 1
    return wbc, rbc, plt


def evaluate(split="test", verbose=False):
    img_dir   = f"TXL-PBC_Dataset/TXL-PBC/images/{split}"
    label_dir = f"TXL-PBC_Dataset/TXL-PBC/labels/{split}"
    img_files = sorted(glob.glob(f"{img_dir}/*.png"))

    gt_wbc = gt_rbc = gt_plt = 0
    pr_wbc = pr_rbc = pr_plt = 0

    for img_path in img_files:
        stem = os.path.splitext(os.path.basename(img_path))[0]
        lbl  = f"{label_dir}/{stem}.txt"
        img  = cv2.imread(img_path)
        w_gt, r_gt, p_gt = load_gt(lbl)
        w_pr, r_pr, p_pr, _ = detect_cells(img)

        gt_wbc += w_gt; gt_rbc += r_gt; gt_plt += p_gt
        pr_wbc += w_pr; pr_rbc += r_pr; pr_plt += p_pr

        if verbose:
            print(f"  {stem[:20]}  WBC {w_gt}->{w_pr}  RBC {r_gt}->{r_pr}  PLT {p_gt}->{p_pr}")

    def err(gt, pr):
        if gt == 0:
            return 0.0 if pr == 0 else float('inf')
        return (pr - gt) / gt

    we = err(gt_wbc, pr_wbc)
    re = err(gt_rbc, pr_rbc)
    pe = err(gt_plt, pr_plt)

    print(f"\n{'='*52}")
    print(f"  Split: {split}   Images: {len(img_files)}")
    print(f"{'='*52}")
    print(f"{'Cell':<6} {'GT':>6} {'Pred':>6} {'Error':>8}  Status")
    print(f"{'-'*52}")
    for name, gt, pr, e in [("WBC", gt_wbc, pr_wbc, we),
                             ("RBC", gt_rbc, pr_rbc, re),
                             ("PLT", gt_plt, pr_plt, pe)]:
        status = "OK" if abs(e) <= 0.30 else ("OVER" if e > 0 else "UNDER")
        print(f"{name:<6} {gt:>6} {pr:>6} {e:>+8.1%}  {status}")
    print(f"{'='*52}")
    return we, re, pe


if __name__ == "__main__":
    evaluate("test")
