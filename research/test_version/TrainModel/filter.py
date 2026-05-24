import numpy as np
from pathlib import Path

FEATURES_DIR = Path("Features")

def delete_frames(sequence: np.ndarray, path):
    seq = sequence.copy()

    LEFT_HAND = slice(18,81)
    RIGHT_HAND = slice(81,144)

    left_nan = np.isnan(seq[:,LEFT_HAND]).any(axis=1)
    right_nan = np.isnan(seq[:,RIGHT_HAND]).any(axis=1)
    both_nan = left_nan & right_nan

    seq_filtered = seq[~both_nan]

    print(f"Before: {seq.shape}     --->    After: {seq_filtered.shape}     {path}")
    np.save(path, seq_filtered)

def frame_filter():
    for gesture_dir in sorted(FEATURES_DIR.iterdir()):
            if not gesture_dir.is_dir():
                continue

            files = list(gesture_dir.glob("*.npy"))

            for path in files:
                seq = np.load(path)
                seq_filtred = delete_frames(seq, path)

if __name__ == "__main__":
    frame_filter()