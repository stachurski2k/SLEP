import numpy as np
from pathlib import Path

FEATURES_DIR = Path("Features")

def trim_frames(sequence: np.ndarray, path):
    seq = sequence.copy()

    LEFT_HAND = slice(18,81)
    RIGHT_HAND = slice(81,144)

    left_nan = np.isnan(seq[:,LEFT_HAND]).any(axis=1)
    right_nan = np.isnan(seq[:,RIGHT_HAND]).any(axis=1)
    both_nan = left_nan & right_nan
    
    has_hand = ~both_nan 

    if not np.any(has_hand):
        seq_filtered = seq[0:0] 
    else:
        valid_indices = np.where(has_hand)[0]

        start_idx = valid_indices[0]
        end_idx = valid_indices[-1]
        
        seq_filtered = seq[start_idx:end_idx+1]

    print(f"Before: {seq.shape}     --->    After: {seq_filtered.shape}     {path}")
    np.save(path, seq_filtered)

def frame_filter():
    for gesture_dir in sorted(FEATURES_DIR.iterdir()):
            if not gesture_dir.is_dir():
                continue

            files = list(gesture_dir.glob("*.npy"))

            for path in files:
                seq = np.load(path)
                seq_filtred = trim_frames(seq, path)

if __name__ == "__main__":
    frame_filter()