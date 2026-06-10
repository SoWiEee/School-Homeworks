"""依助教規格進行 IoU 評估。

GT（YOLO 正規化格式）-> 含邊界裁切的像素框。當預測框與 GT 框
屬於同一類別且 IoU 超過閥值時，使用一對一貪婪比對（IoU 最高的配對優先），
視為真陽性（TP）。回報各類別與 micro 的 Precision / Recall / F1。

使用方式：
    python eval_iou.py --split test --iou 0.5 --mode improved
"""
from __future__ import annotations

import argparse
import glob
import os
from typing import Dict, List, Tuple

import cv2

from blood_cell_detector import (
    CLASS_NAMES,
    detect_cells,
    load_image,
    load_platelet_model,
)

Box = List[float]  # [class, x1, y1, x2, y2]


def load_yolo_gt_clipped(img_path: str, dataset_root: str, w: int, h: int) -> List[Box]:
    """YOLO 正規化標註 -> 像素框，裁切至影像邊界內。"""
    split = os.path.basename(os.path.dirname(img_path))
    label_path = os.path.join(
        dataset_root, "labels", split,
        os.path.basename(img_path).replace(".png", ".txt"),
    )
    boxes: List[Box] = []
    if not os.path.exists(label_path):
        return boxes
    with open(label_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            c, xc, yc, bw, bh = map(float, line.split())
            xmin = round((xc - bw / 2) * w)
            ymin = round((yc - bh / 2) * h)
            xmax = round((xc + bw / 2) * w)
            ymax = round((yc + bh / 2) * h)
            # 邊界裁切
            xmin = max(0, min(xmin, w))
            ymin = max(0, min(ymin, h))
            xmax = max(0, min(xmax, w))
            ymax = max(0, min(ymax, h))
            boxes.append([int(c), float(xmin), float(ymin), float(xmax), float(ymax)])
    return boxes


def iou(box_a: Box, box_b: Box) -> float:
    x_left = max(box_a[1], box_b[1])
    y_top = max(box_a[2], box_b[2])
    x_right = min(box_a[3], box_b[3])
    y_bottom = min(box_a[4], box_b[4])
    iw = max(0.0, x_right - x_left)
    ih = max(0.0, y_bottom - y_top)
    inter = iw * ih
    area_a = (box_a[3] - box_a[1]) * (box_a[4] - box_a[2])
    area_b = (box_b[3] - box_b[1]) * (box_b[4] - box_b[2])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def match_one_to_one(preds: List[Box], gts: List[Box], thr: float) -> Tuple[int, int, int]:
    """依 IoU 由高到低的貪婪一對一比對，僅比對同類別。"""
    pairs = []
    for pi, p in enumerate(preds):
        for gi, g in enumerate(gts):
            if int(p[0]) != int(g[0]):
                continue
            score = iou(p, g)
            if score >= thr:
                pairs.append((score, pi, gi))
    pairs.sort(reverse=True)
    used_p, used_g = set(), set()
    tp = 0
    for score, pi, gi in pairs:
        if pi in used_p or gi in used_g:
            continue
        used_p.add(pi)
        used_g.add(gi)
        tp += 1
    fp = len(preds) - tp
    fn = len(gts) - tp
    return tp, fp, fn


def evaluate(dataset_root: str, split: str, mode: str, model, thr: float):
    paths = sorted(glob.glob(os.path.join(dataset_root, "images", split, "*.png")))
    totals = {c: [0, 0, 0] for c in (0, 1, 2)}  # tp（真陽性）, fp（假陽性）, fn（假陰性）
    for path in paths:
        img = load_image(path)
        h, w = img.shape[:2]
        gts = load_yolo_gt_clipped(path, dataset_root, w, h)
        preds = detect_cells(img, mode=mode, platelet_model=model)
        for c in (0, 1, 2):
            ps = [b for b in preds if int(b[0]) == c]
            gs = [b for b in gts if int(b[0]) == c]
            tp, fp, fn = match_one_to_one(ps, gs, thr)
            totals[c][0] += tp
            totals[c][1] += fp
            totals[c][2] += fn
    return totals


def report(totals, thr):
    print(f"IoU threshold = {thr}")
    print("class,tp,fp,fn,precision,recall,f1")
    micro = [0, 0, 0]
    for c in (0, 1, 2):
        tp, fp, fn = totals[c]
        micro[0] += tp
        micro[1] += fp
        micro[2] += fn
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * p * r / (p + r) if p + r else 0.0
        print(f"{CLASS_NAMES[c]},{tp},{fp},{fn},{p:.4f},{r:.4f},{f1:.4f}")
    tp, fp, fn = micro
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    print(f"micro,{tp},{fp},{fn},{p:.4f},{r:.4f},{f1:.4f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="TXL-PBC_Dataset/TXL-PBC")
    ap.add_argument("--split", default="test", choices=["train", "val", "test"])
    ap.add_argument("--iou", type=float, default=0.5)
    ap.add_argument("--mode", default="improved", choices=["improved", "rule"])
    ap.add_argument("--model", default="et_platelet_model.pkl")
    args = ap.parse_args()

    mode = "Improved classical" if args.mode == "improved" else "Rule-based only"
    model = load_platelet_model(args.model) if os.path.exists(args.model) else None
    totals = evaluate(args.root, args.split, mode, model, args.iou)
    report(totals, args.iou)


if __name__ == "__main__":
    main()
