"""Analyze pixel statistics within GT bboxes for calibration."""
import cv2, numpy as np, glob, os

test_imgs = sorted(glob.glob('TXL-PBC_Dataset/TXL-PBC/images/test/*.png'))
label_dir = 'TXL-PBC_Dataset/TXL-PBC/labels/test'

wbc_data, rbc_data, plt_data = [], [], []

for img_path in test_imgs:
    stem = os.path.splitext(os.path.basename(img_path))[0]
    lbl = label_dir + '/' + stem + '.txt'
    if not os.path.exists(lbl): continue
    img = cv2.imread(img_path)
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv  = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    with open(lbl) as f:
        for line in f:
            parts = line.split()
            cls = int(parts[0])
            cx, cy, bw, bh = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
            x1 = max(0, int((cx - bw/2)*w)); x2 = min(w, int((cx + bw/2)*w))
            y1 = max(0, int((cy - bh/2)*h)); y2 = min(h, int((cy + bh/2)*h))
            rg = gray[y1:y2, x1:x2]
            rh = hsv[y1:y2, x1:x2]
            if rg.size == 0: continue
            rec = {
                'gmin': int(rg.min()), 'gmax': int(rg.max()),
                'gmed': float(np.median(rg)),
                'Hmed': float(np.median(rh[:,:,0])),
                'Smed': float(np.median(rh[:,:,1])),
                'Vmed': float(np.median(rh[:,:,2])),
                'area': (x2-x1)*(y2-y1)
            }
            if cls == 0: wbc_data.append(rec)
            elif cls == 1: rbc_data.append(rec)
            elif cls == 2: plt_data.append(rec)

def summary(name, data):
    print(f"\n=== {name} (n={len(data)}) ===")
    for key in ['gmin','gmax','gmed','Hmed','Smed','Vmed']:
        vals = [d[key] for d in data]
        print(f"  {key:6s}: min={min(vals):.1f}  max={max(vals):.1f}  med={np.median(vals):.1f}")

summary("WBC", wbc_data)
summary("RBC", rbc_data)
summary("PLT", plt_data)

print("\n--- All PLT samples ---")
for s in plt_data:
    print(f"  gray {s['gmin']:3d}-{s['gmax']:3d} med={s['gmed']:.0f}  HSV H={s['Hmed']:.0f} S={s['Smed']:.0f} V={s['Vmed']:.0f}  area={s['area']}px")
