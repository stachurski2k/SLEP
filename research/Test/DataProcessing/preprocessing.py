# preprocessing.py
import numpy as np
from scipy.interpolate import interp1d

# ciało: indeksy 0-17 (6 punktów: barki, łokcie, nadgarstki)
LEFT_SHOULDER  = slice(0*3, 0*3+3)   # 0:3
RIGHT_SHOULDER = slice(1*3, 1*3+3)   # 3:6

# sprawdź czy barki są w kadrze (wartości MediaPipe: 0-1)
# jeśli nie — użyj nadgarstków jako fallback
LEFT_WRIST     = slice(4*3, 4*3+3)   # 12:15
RIGHT_WRIST    = slice(5*3, 5*3+3)   # 15:18

def fill_missing_hands(sequence: np.ndarray,
                       nan_threshold=0.10) -> np.ndarray:
    result = sequence.copy()

    LEFT_WRIST_POSE  = slice(12, 15)
    RIGHT_WRIST_POSE = slice(15, 18)
    LEFT_HAND        = slice(18, 81)
    RIGHT_HAND       = slice(81, 144)

    left_nan_ratio  = np.isnan(sequence[:, LEFT_HAND]).any(axis=1).mean()
    right_nan_ratio = np.isnan(sequence[:, RIGHT_HAND]).any(axis=1).mean()

    for t in range(len(sequence)):
        # lewa ręka
        if left_nan_ratio > nan_threshold:
            if np.isnan(sequence[t, LEFT_HAND]).all():
                wrist = sequence[t, LEFT_WRIST_POSE]
                if not np.isnan(wrist).any():
                    for i in range(21):
                        result[t, 18 + i*3 : 18 + i*3 + 3] = wrist

        # prawa ręka
        if right_nan_ratio > nan_threshold:
            if np.isnan(sequence[t, RIGHT_HAND]).all():
                wrist = sequence[t, RIGHT_WRIST_POSE]
                if not np.isnan(wrist).any():
                    for i in range(21):
                        result[t, 81 + i*3 : 81 + i*3 + 3] = wrist

    return result


def interpolate_missing(sequence: np.ndarray) -> np.ndarray:
    result = sequence.copy()
    for dim in range(sequence.shape[1]):
        col      = sequence[:, dim]
        nan_mask = np.isnan(col)
        if nan_mask.all():
            result[:, dim] = 0.0
            continue
        if not nan_mask.any():
            continue
        indices        = np.arange(len(col))
        valid          = ~nan_mask
        result[:, dim] = np.interp(indices, indices[valid], col[valid])
    return result

def remove_static_frames(sequence: np.ndarray,
                         threshold=0.01) -> np.ndarray:
    motion      = np.linalg.norm(np.diff(sequence, axis=0), axis=1)
    dynamic_idx = np.where(motion > threshold)[0]
    if len(dynamic_idx) < 10:
        return sequence
    return sequence[dynamic_idx]


def normalize(sequence: np.ndarray) -> np.ndarray:
    normalized = sequence.copy().astype(np.float32)

    left_sh  = normalized[:, LEFT_SHOULDER]   
    right_sh = normalized[:, RIGHT_SHOULDER]  

    center = (left_sh + right_sh) / 2  

    for i in range(0, normalized.shape[1], 3):
        normalized[:, i:i+3] -= center

    shoulder_dist = np.linalg.norm(
        normalized[:, LEFT_SHOULDER] - normalized[:, RIGHT_SHOULDER],
        axis=1
    ).mean() + 1e-8

    normalized /= shoulder_dist
    return normalized


def resample(sequence: np.ndarray, target_len=60) -> np.ndarray:
    n, dims = sequence.shape
    if n == target_len:
        return sequence
    old_t = np.linspace(0, 1, n)
    new_t = np.linspace(0, 1, target_len)
    resampled = np.zeros((target_len, dims), dtype=np.float32)
    for d in range(dims):
        f = interp1d(old_t, sequence[:, d], kind="linear")
        resampled[:, d] = f(new_t)
    return resampled


def preprocess(sequence: np.ndarray, target_len=60) -> np.ndarray:
    sequence = fill_missing_hands(sequence) 
    sequence = interpolate_missing(sequence)
    sequence = remove_static_frames(sequence)
    sequence = normalize(sequence)
    sequence = resample(sequence, target_len)
    return sequence