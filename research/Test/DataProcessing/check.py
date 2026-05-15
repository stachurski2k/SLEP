import numpy as np
from pathlib import Path

FEATURES_DIR = Path("Features")

LEFT_HAND  = slice(18, 81)
RIGHT_HAND = slice(81, 144)

stats = {}
for gesture_dir in sorted(FEATURES_DIR.iterdir()):
    if not gesture_dir.is_dir():
        continue
    
    pliki = list(gesture_dir.glob("*.npy"))
    nan_counts = {"ok": 0, "czesciowe": 0, "slabe": 0}
    
    for path in pliki:
        seq = np.load(path)
        left_nan  = np.isnan(seq[:, LEFT_HAND]).any(axis=1).mean()
        right_nan = np.isnan(seq[:, RIGHT_HAND]).any(axis=1).mean()
        worst     = max(left_nan, right_nan)
        
        if worst < 0.3:
            nan_counts["ok"] += 1
        elif worst < 0.7:
            nan_counts["czesciowe"] += 1
        else:
            nan_counts["slabe"] += 1
    
    stats[gesture_dir.name] = nan_counts
    print(f"{gesture_dir.name:15s}  "
          f"ok: {nan_counts['ok']:2d}  "
          f"częściowe: {nan_counts['czesciowe']:2d}  "
          f"słabe: {nan_counts['slabe']:2d}  "
          f"/ {len(pliki)}")