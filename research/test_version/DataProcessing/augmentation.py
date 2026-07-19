import numpy as np


# ── LANDMARK SLICES (matching preprocessing.py) ───────────────────────────
LEFT_SHOULDER  = slice(0, 3)
RIGHT_SHOULDER = slice(3, 6)
LEFT_ELBOW     = slice(6, 9)
RIGHT_ELBOW    = slice(9, 12)
LEFT_WRIST     = slice(12, 15)
RIGHT_WRIST    = slice(15, 18)
LEFT_HAND      = slice(18, 81)
RIGHT_HAND     = slice(81, 144)


def gaussian_noise(sequence: np.ndarray, std=0.02) -> np.ndarray:
    noise = np.random.normal(0.0, std, sequence.shape).astype(np.float32)
    return sequence + noise


def temporal_stretch(sequence: np.ndarray, min_factor=0.8, max_factor=1.2) -> np.ndarray:
    T, F = sequence.shape
    factor = np.random.uniform(min_factor, max_factor)
    new_T = max(4, int(T * factor))

    src_t = np.linspace(0, 1, T)
    dst_t = np.linspace(0, 1, new_T)
    stretched = np.stack(
        [np.interp(dst_t, src_t, sequence[:, f]) for f in range(F)],
        axis=1
    ).astype(np.float32)

    if new_T >= T:
        start = np.random.randint(0, new_T - T + 1)
        return stretched[start:start + T]
    else:
        pad = np.repeat(stretched[[-1]], T - new_T, axis=0)
        return np.concatenate([stretched, pad], axis=0)


def temporal_warp(sequence: np.ndarray, num_knots=4, std=0.1) -> np.ndarray:
    T, F = sequence.shape
    knot_x = np.linspace(0, 1, num_knots + 2)
    knot_y = knot_x + np.concatenate([[0], np.random.uniform(-std, std, num_knots), [0]])
    knot_y = np.clip(knot_y, 0, 1)
    knot_y[0], knot_y[-1] = 0.0, 1.0

    knot_y = np.maximum.accumulate(knot_y)

    src_t = np.linspace(0, 1, T)
    warped_t = np.interp(src_t, knot_x, knot_y)

    return np.stack(
        [np.interp(warped_t, src_t, sequence[:, f]) for f in range(F)],
        axis=1
    ).astype(np.float32)


def random_scale(sequence: np.ndarray, min_scale=0.9, max_scale=1.1) -> np.ndarray:

    scale = np.random.uniform(min_scale, max_scale)
    return (sequence * scale).astype(np.float32)


def mirror_horizontal(sequence: np.ndarray) -> np.ndarray:
    seq = sequence.copy()
    seq[:, 0::3] *= -1.0  # negate every X component

    # swap left ↔ right hand blocks
    left_copy  = seq[:, LEFT_HAND].copy()
    right_copy = seq[:, RIGHT_HAND].copy()
    seq[:, LEFT_HAND]  = right_copy
    seq[:, RIGHT_HAND] = left_copy

    # swap left ↔ right shoulder
    left_sh  = seq[:, LEFT_SHOULDER].copy()
    right_sh = seq[:, RIGHT_SHOULDER].copy()
    seq[:, LEFT_SHOULDER]  = right_sh
    seq[:, RIGHT_SHOULDER] = left_sh

    # swap left ↔ right elbow
    left_elb = seq[:, LEFT_ELBOW].copy()
    right_elb = seq[:, RIGHT_ELBOW].copy()
    seq[:, LEFT_ELBOW]  = right_elb
    seq[:, RIGHT_ELBOW] = left_elb

    # swap left ↔ right wrist
    left_wr = seq[:, LEFT_WRIST].copy()
    right_wr = seq[:, RIGHT_WRIST].copy()
    seq[:, LEFT_WRIST]  = right_wr
    seq[:, RIGHT_WRIST] = left_wr

    return seq.astype(np.float32)


def landmark_dropout(sequence: np.ndarray, drop_prob=0.05) -> np.ndarray:
    seq = sequence.copy()
    # operate on landmark triplets
    num_landmarks = sequence.shape[1] // 3
    for lm in range(num_landmarks):
        if np.random.random() < drop_prob:
            seq[:, lm*3 : lm*3+3] = 0.0
    return seq.astype(np.float32)


# ── COMPOSE ───────────────────────────────────────────────────────────────

class SequenceAugmentor:
    def __init__(
        self,
        noise_std     = 0.02,
        stretch_range = (0.85, 1.15),
        warp_prob     = 0.5,
        warp_knots    = 4,
        warp_std      = 0.08,
        scale_range   = (0.9, 1.1),
        mirror_prob   = 0.5,
        dropout_prob  = 0.05,
    ):
        self.noise_std     = noise_std
        self.stretch_range = stretch_range
        self.warp_prob     = warp_prob
        self.warp_knots    = warp_knots
        self.warp_std      = warp_std
        self.scale_range   = scale_range
        self.mirror_prob   = mirror_prob
        self.dropout_prob  = dropout_prob

    def __call__(self, sequence: np.ndarray) -> np.ndarray:
        seq = sequence.copy()

        # 1. Gaussian noise
        if self.noise_std > 0:
            seq = gaussian_noise(seq, std=self.noise_std)

        # 2. Temporal stretch
        if self.stretch_range is not None:
            seq = temporal_stretch(seq, *self.stretch_range)

        # 3. Temporal warp (random time axis distortion)
        if np.random.random() < self.warp_prob:
            seq = temporal_warp(seq, num_knots=self.warp_knots, std=self.warp_std)

        # 4. Scale
        if self.scale_range is not None:
            seq = random_scale(seq, *self.scale_range)

        # 5. Mirror
        if np.random.random() < self.mirror_prob:
            seq = mirror_horizontal(seq)

        # 6. Landmark dropout
        if self.dropout_prob > 0:
            seq = landmark_dropout(seq, drop_prob=self.dropout_prob)

        return seq
