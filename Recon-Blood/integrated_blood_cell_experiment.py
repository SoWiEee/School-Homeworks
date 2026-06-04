"""
Integrated Blood Smear Image Processing Experiment
==================================================

This script is an experiment-only version.
It does not use Streamlit yet.

It demonstrates:
1. Required preprocessing pipeline:
   - Gray
   - Gaussian Blur
   - Adaptive Thresholding
   - Morphological Closing

2. Rule-based detection branches:
   - WBC detection:
     HSV purple mask + morphology + contour selection
   - RBC detection:
     Hough Circle Transform + RBC color validation + WBC exclusion
   - Platelet detection:
     conservative small purple object detection + WBC exclusion

No deep learning is used.

Usage:
    python integrated_blood_cell_experiment.py --input BCCD --output experiment_output

Single image:
    python integrated_blood_cell_experiment.py --input BCCD/BloodImage_00000.jpg --output experiment_output

Use per-image RBC Hough tuning for BloodImage_00000 ~ BloodImage_00004:
    python integrated_blood_cell_experiment.py --input BCCD --output experiment_output --use-tuned-rbc
"""

import argparse
import csv
from pathlib import Path

import cv2
import numpy as np


# ============================================================
# Utility
# ============================================================

def make_kernel(size: int) -> np.ndarray:
    size = int(size)
    if size % 2 == 0:
        size += 1
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))


def collect_image_paths(input_path: str | Path) -> list[Path]:
    input_path = Path(input_path)

    if input_path.is_file():
        return [input_path]

    if not input_path.is_dir():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

    return sorted([
        p for p in input_path.iterdir()
        if p.suffix.lower() in extensions
    ])


# ============================================================
# Required Preprocessing Pipeline
# ============================================================

def required_pipeline(bgr: np.ndarray) -> dict:
    """
    Required preprocessing pipeline:
    gray -> Gaussian blur -> adaptive threshold -> morphological closing
    """
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    blur = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    adaptive = cv2.adaptiveThreshold(
        blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        7
    )

    closing = cv2.morphologyEx(
        adaptive,
        cv2.MORPH_CLOSE,
        make_kernel(5),
        iterations=1
    )

    return {
        "gray": gray,
        "blur": blur,
        "adaptive": adaptive,
        "closing": closing
    }


# ============================================================
# WBC Detection
# ============================================================

def detect_wbc(bgr: np.ndarray) -> dict:
    """
    Detect WBC using purple/blue-purple nucleus color.

    WBC rule:
    1. HSV purple threshold.
    2. Morphological opening to remove tiny noise.
    3. Dilation + closing to merge separated nucleus lobes.
    4. Contour clustering.
    5. Select large non-border candidate if available.
    """
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

    purple = cv2.inRange(
        hsv,
        np.array((100, 60, 50)),
        np.array((170, 255, 210))
    )

    purple = cv2.morphologyEx(
        purple,
        cv2.MORPH_OPEN,
        make_kernel(3),
        iterations=1
    )

    merged = cv2.dilate(
        purple,
        make_kernel(15),
        iterations=1
    )

    merged = cv2.morphologyEx(
        merged,
        cv2.MORPH_CLOSE,
        make_kernel(15),
        iterations=1
    )

    img_h, img_w = merged.shape
    contours, _ = cv2.findContours(
        merged,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    raw_candidates = []

    for contour in contours:
        area = cv2.contourArea(contour)

        if area < 500:
            continue

        x, y, w, h = cv2.boundingRect(contour)
        touches = x <= 1 or y <= 1 or x + w >= img_w - 1 or y + h >= img_h - 1

        m = cv2.moments(contour)

        if m["m00"]:
            cx = m["m10"] / m["m00"]
            cy = m["m01"] / m["m00"]
        else:
            cx = x + w / 2
            cy = y + h / 2

        raw_candidates.append({
            "contour": contour,
            "area": float(area),
            "bbox": (x, y, w, h),
            "touches": touches,
            "center": (cx, cy)
        })

    visited = [False] * len(raw_candidates)
    clusters = []

    for i in range(len(raw_candidates)):
        if visited[i]:
            continue

        stack = [i]
        visited[i] = True
        cluster = []

        while stack:
            current = stack.pop()
            cluster.append(current)
            x1, y1 = raw_candidates[current]["center"]

            for j in range(len(raw_candidates)):
                if visited[j]:
                    continue

                x2, y2 = raw_candidates[j]["center"]
                dist = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

                if dist < 140:
                    visited[j] = True
                    stack.append(j)

        clusters.append(cluster)

    hulls = []

    for cluster in clusters:
        points = np.vstack([raw_candidates[i]["contour"] for i in cluster])
        hull = cv2.convexHull(points)
        area = cv2.contourArea(hull)

        x, y, w, h = cv2.boundingRect(hull)
        touches = x <= 1 or y <= 1 or x + w >= img_w - 1 or y + h >= img_h - 1

        hulls.append({
            "hull": hull,
            "area": float(area),
            "bbox": (x, y, w, h),
            "touches": touches
        })

    non_border = [
        h for h in hulls
        if not h["touches"] and h["area"] >= 6000
    ]

    border = [
        h for h in hulls
        if h["touches"] and h["area"] >= 6000
    ]

    if non_border:
        selected = max(non_border, key=lambda h: h["area"])
        status = "full_wbc"
    elif border:
        selected = max(border, key=lambda h: h["area"])
        status = "partial_wbc_border"
    elif hulls:
        selected = max(hulls, key=lambda h: h["area"])
        status = "no_confident_wbc"
    else:
        selected = None
        status = "no_candidate"

    return {
        "purple_mask": purple,
        "merged_mask": merged,
        "hulls": hulls,
        "selected": selected,
        "status": status
    }


# ============================================================
# RBC Detection
# ============================================================

RBC_TUNED_PARAM2 = {
    "BloodImage_00000.jpg": 30,
    "BloodImage_00001.jpg": 28,
    "BloodImage_00002.jpg": 28,
    "BloodImage_00003.jpg": 28,
    "BloodImage_00004.jpg": 26,
}


def detect_rbc(bgr: np.ndarray, param2: float = 28) -> dict:
    """
    Detect RBC using Hough Circle Transform + color validation.

    RBC rule:
    1. CLAHE enhancement on grayscale.
    2. Median blur.
    3. Hough Circle Transform.
    4. Build pink/red RBC color mask using HSV + Lab.
    5. Exclude WBC purple region.
    6. Keep circles with enough RBC color overlap.
    """
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    enhanced = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    ).apply(gray)

    blurred = cv2.medianBlur(enhanced, 5)

    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=35,
        param1=50,
        param2=param2,
        minRadius=18,
        maxRadius=55
    )

    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)

    h, s, v = cv2.split(hsv)
    L, A, B = cv2.split(lab)

    purple = cv2.inRange(
        hsv,
        np.array((100, 60, 50)),
        np.array((170, 255, 210))
    )

    wbc_exclusion = cv2.dilate(
        purple,
        make_kernel(25),
        iterations=1
    )

    mask_hsv = (
        (((h >= 150) | (h <= 10)) &
         (s >= 8) & (s <= 100) &
         (v >= 100) & (v <= 240))
    ).astype(np.uint8) * 255

    mask_lab = (
        ((A >= 132) &
         (B >= 118) &
         (L >= 110) &
         (L <= 225))
    ).astype(np.uint8) * 255

    rbc_mask = cv2.bitwise_or(mask_hsv, mask_lab)
    rbc_mask[wbc_exclusion > 0] = 0

    rbc_mask = cv2.morphologyEx(
        rbc_mask,
        cv2.MORPH_OPEN,
        make_kernel(3),
        iterations=1
    )

    accepted = []
    raw_count = 0

    if circles is not None:
        circles = np.round(circles[0]).astype(int)
        raw_count = len(circles)
        img_h, img_w = gray.shape

        for x, y, r in circles:
            if x < 0 or y < 0 or x >= img_w or y >= img_h:
                continue

            circle_mask = np.zeros(gray.shape, np.uint8)
            cv2.circle(circle_mask, (x, y), r, 255, -1)

            area = np.sum(circle_mask > 0)

            rbc_ratio = np.sum((rbc_mask > 0) & (circle_mask > 0)) / (area + 1e-6)
            wbc_ratio = np.sum((wbc_exclusion > 0) & (circle_mask > 0)) / (area + 1e-6)

            if wbc_ratio > 0.08:
                continue

            if rbc_ratio < 0.15:
                continue

            accepted.append({
                "x": int(x),
                "y": int(y),
                "r": int(r),
                "rbc_ratio": float(rbc_ratio),
                "wbc_ratio": float(wbc_ratio)
            })

    return {
        "enhanced": enhanced,
        "rbc_mask": rbc_mask,
        "wbc_exclusion": wbc_exclusion,
        "circles": accepted,
        "raw_count": raw_count,
        "param2": param2
    }


# ============================================================
# Platelet Detection
# ============================================================

def detect_platelets(bgr: np.ndarray, wbc_result: dict) -> dict:
    """
    Conservative platelet detection.

    Platelet rule:
    1. Platelets are treated as small, saturated purple objects.
    2. WBC region is aggressively excluded because WBC nuclei are also purple.
    3. Connected components are filtered by area, aspect ratio, and circularity.

    This is intentionally conservative:
    - fewer false positives
    - may miss faint platelets
    """
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

    raw_mask = cv2.inRange(
        hsv,
        np.array((110, 80, 30)),
        np.array((160, 255, 210))
    )

    raw_mask = cv2.morphologyEx(
        raw_mask,
        cv2.MORPH_OPEN,
        make_kernel(3),
        iterations=1
    )

    exclude = np.zeros(raw_mask.shape, np.uint8)

    if wbc_result["selected"] is not None:
        cv2.drawContours(
            exclude,
            [wbc_result["selected"]["hull"]],
            -1,
            255,
            -1
        )

        exclude = cv2.dilate(
            exclude,
            make_kernel(35),
            iterations=1
        )

    platelet_mask = raw_mask.copy()
    platelet_mask[exclude > 0] = 0

    platelet_mask = cv2.morphologyEx(
        platelet_mask,
        cv2.MORPH_OPEN,
        make_kernel(3),
        iterations=1
    )

    contours, _ = cv2.findContours(
        platelet_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    img_h, img_w = platelet_mask.shape
    platelets = []

    for contour in contours:
        area = cv2.contourArea(contour)

        if not (8 <= area <= 250):
            continue

        x, y, w, h = cv2.boundingRect(contour)

        if x <= 1 or y <= 1 or x + w >= img_w - 1 or y + h >= img_h - 1:
            continue

        aspect = w / h if h else 0

        if aspect < 0.35 or aspect > 2.8:
            continue

        perimeter = cv2.arcLength(contour, True)
        circ = 4 * np.pi * area / (perimeter * perimeter) if perimeter else 0

        if circ < 0.2:
            continue

        m = cv2.moments(contour)

        if m["m00"]:
            cx = int(m["m10"] / m["m00"])
            cy = int(m["m01"] / m["m00"])
        else:
            cx = x + w // 2
            cy = y + h // 2

        platelets.append({
            "contour": contour,
            "area": float(area),
            "bbox": (x, y, w, h),
            "center": (cx, cy),
            "circularity": float(circ)
        })

    return {
        "raw_mask": raw_mask,
        "exclude_mask": exclude,
        "platelet_mask": platelet_mask,
        "platelets": platelets
    }


# ============================================================
# Visualization
# ============================================================

def draw_integrated_overlay(
    bgr: np.ndarray,
    wbc: dict,
    rbc: dict,
    platelets: dict
) -> np.ndarray:
    overlay = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    # WBC: hull + bounding box
    if wbc["selected"] is not None and wbc["status"] in ("full_wbc", "partial_wbc_border"):
        color = (0, 255, 0) if wbc["status"] == "full_wbc" else (255, 165, 0)
        cv2.drawContours(overlay, [wbc["selected"]["hull"]], -1, color, 3)

        x, y, w, h = wbc["selected"]["bbox"]
        cv2.rectangle(
            overlay,
            (x, y),
            (x + w, y + h),
            (255, 0, 0),
            2
        )

    # RBC: circles
    for circle in rbc["circles"]:
        cv2.circle(
            overlay,
            (circle["x"], circle["y"]),
            circle["r"],
            (0, 255, 0),
            2
        )

        cv2.circle(
            overlay,
            (circle["x"], circle["y"]),
            2,
            (255, 0, 0),
            2
        )

    # Platelets: cyan boxes
    for p in platelets["platelets"]:
        x, y, w, h = p["bbox"]
        cx, cy = p["center"]

        cv2.rectangle(
            overlay,
            (x, y),
            (x + w, y + h),
            (0, 255, 255),
            2
        )

        cv2.circle(
            overlay,
            (cx, cy),
            3,
            (0, 255, 255),
            -1
        )

    wbc_count = 1 if wbc["status"] in ("full_wbc", "partial_wbc_border") else 0

    cv2.putText(
        overlay,
        f"WBC={wbc_count}  RBC={len(rbc['circles'])}  Platelet={len(platelets['platelets'])}",
        (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 0),
        2,
        cv2.LINE_AA
    )

    return overlay


# ============================================================
# Full Experiment
# ============================================================

def process_image(
    image_path: Path,
    output_dir: Path,
    use_tuned_rbc: bool
) -> dict:
    bgr = cv2.imread(str(image_path))

    if bgr is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")

    pipeline = required_pipeline(bgr)
    wbc = detect_wbc(bgr)

    if use_tuned_rbc:
        param2 = RBC_TUNED_PARAM2.get(image_path.name, 28)
    else:
        param2 = 28

    rbc = detect_rbc(bgr, param2=param2)
    platelet = detect_platelets(bgr, wbc)
    overlay = draw_integrated_overlay(bgr, wbc, rbc, platelet)

    stem = image_path.stem

    cv2.imwrite(str(output_dir / f"{stem}_gray.png"), pipeline["gray"])
    cv2.imwrite(str(output_dir / f"{stem}_gaussian_blur.png"), pipeline["blur"])
    cv2.imwrite(str(output_dir / f"{stem}_adaptive_threshold.png"), pipeline["adaptive"])
    cv2.imwrite(str(output_dir / f"{stem}_morph_closing.png"), pipeline["closing"])

    cv2.imwrite(str(output_dir / f"{stem}_wbc_mask.png"), wbc["merged_mask"])
    cv2.imwrite(str(output_dir / f"{stem}_rbc_mask.png"), rbc["rbc_mask"])
    cv2.imwrite(str(output_dir / f"{stem}_platelet_mask.png"), platelet["platelet_mask"])
    cv2.imwrite(str(output_dir / f"{stem}_integrated_overlay.png"), cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))

    return {
        "file": image_path.name,
        "wbc_status": wbc["status"],
        "wbc_count": 1 if wbc["status"] in ("full_wbc", "partial_wbc_border") else 0,
        "rbc_count": len(rbc["circles"]),
        "platelet_count": len(platelet["platelets"]),
        "rbc_param2": param2
    }


def run_batch(args: argparse.Namespace) -> None:
    image_paths = collect_image_paths(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = []

    for image_path in image_paths:
        row = process_image(
            image_path=image_path,
            output_dir=output_dir,
            use_tuned_rbc=args.use_tuned_rbc
        )

        rows.append(row)

        print(
            f"{row['file']}: "
            f"WBC={row['wbc_count']} "
            f"RBC={row['rbc_count']} "
            f"Platelet={row['platelet_count']} "
            f"WBC status={row['wbc_status']}"
        )

    summary_path = output_dir / "integrated_summary.csv"

    with open(summary_path, "w", newline="", encoding="utf-8-sig") as f:
        fieldnames = [
            "file",
            "wbc_status",
            "wbc_count",
            "rbc_count",
            "platelet_count",
            "rbc_param2"
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved summary: {summary_path}")
    print(f"Saved stage images to: {output_dir}")


# ============================================================
# CLI
# ============================================================

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Integrated traditional image processing experiment for WBC/RBC/platelet detection."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Input image file or folder path."
    )

    parser.add_argument(
        "--output",
        default="integrated_output",
        help="Output folder. Default: integrated_output"
    )

    parser.add_argument(
        "--use-tuned-rbc",
        action="store_true",
        help="Use per-image RBC Hough param2 for BloodImage_00000 ~ BloodImage_00004."
    )

    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    run_batch(args)


if __name__ == "__main__":
    main()
