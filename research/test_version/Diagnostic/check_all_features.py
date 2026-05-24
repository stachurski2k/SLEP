import numpy as np
from pathlib import Path

FEATURES_DIR = Path("Features")

LEFT_HAND  = slice(18, 81)
RIGHT_HAND = slice(81, 144)

for gesture_dir in sorted(FEATURES_DIR.iterdir()):
    if not gesture_dir.is_dir():
        continue

    files = list(gesture_dir.glob("*.npy"))
    nan_counts = {"good": 0, "ok": 0, "bad": 0}

    for path in files:
        seq       = np.load(path)
        left_nan  = np.isnan(seq[:, LEFT_HAND]).any(axis=1).mean()
        right_nan = np.isnan(seq[:, RIGHT_HAND]).any(axis=1).mean()
        worst     = max(left_nan, right_nan)

        if worst < 0.25:
            nan_counts["good"] += 1
        elif worst < 0.5:
            nan_counts["ok"] += 1
        else:
            nan_counts["bad"] += 1

    print(f"{gesture_dir.name:15s}  "
          f"good (<25%): {nan_counts['good']:2d}  "
          f"ok (25-50%): {nan_counts['ok']:2d}  "
          f"bad (>50%):  {nan_counts['bad']:2d}  "
          f"/ {len(files)}")