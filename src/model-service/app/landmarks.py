"""Landmark extraction and preprocessing.

Ported from research/test_version/DataProcessing/collector.py and
preprocessing.py, trimmed to the single-video, inference-only path (no
dataset scanning, no augmentation).
"""
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter

# --- MediaPipe landmark extraction -----------------------------------------

BaseOptions = mp.tasks.BaseOptions
RunningMode = mp.tasks.vision.RunningMode
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions

POSE_KEY_POINTS = [11, 12, 13, 14, 15, 16]
LEFT_WRIST_POSE_INDEX = 15
RIGHT_WRIST_POSE_INDEX = 16
FEATURE_SIZE = 144


def create_landmarkers(hand_model_path: Path, pose_model_path: Path):
    hands_options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(hand_model_path)),
        running_mode=RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.25,
        min_hand_presence_confidence=0.25,
        min_tracking_confidence=0.3,
    )

    pose_options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(pose_model_path)),
        running_mode=RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
        output_segmentation_masks=False,
    )

    return (
        HandLandmarker.create_from_options(hands_options),
        PoseLandmarker.create_from_options(pose_options),
    )


def landmark_xy_distance(hand_landmarks, pose_landmark) -> float:
    wrist = hand_landmarks[0]
    return float(np.hypot(wrist.x - pose_landmark.x, wrist.y - pose_landmark.y))


def extract_landmarks(hands_result, pose_result) -> np.ndarray:
    features = []
    pose_landmarks = None

    if pose_result.pose_landmarks:
        pose_landmarks = pose_result.pose_landmarks[0]
        for idx in POSE_KEY_POINTS:
            lm = pose_landmarks[idx]
            features.extend([lm.x, lm.y, lm.z])
    else:
        features.extend([np.nan] * 18)

    left_hand = None
    right_hand = None
    detected_hands = []

    for hand_landmarks, handedness in zip(
        hands_result.hand_landmarks,
        hands_result.handedness,
    ):
        label = handedness[0].category_name
        coords = np.array(
            [[lm.x, lm.y, lm.z] for lm in hand_landmarks],
            dtype=np.float32,
        ).flatten()
        detected_hands.append((hand_landmarks, label, coords))

    if pose_landmarks and len(detected_hands) == 1:
        hand_landmarks, _, coords = detected_hands[0]
        left_dist = landmark_xy_distance(
            hand_landmarks,
            pose_landmarks[LEFT_WRIST_POSE_INDEX],
        )
        right_dist = landmark_xy_distance(
            hand_landmarks,
            pose_landmarks[RIGHT_WRIST_POSE_INDEX],
        )

        if left_dist <= right_dist:
            left_hand = coords
        else:
            right_hand = coords

    elif pose_landmarks and len(detected_hands) == 2:
        first_hand, _, first_coords = detected_hands[0]
        second_hand, _, second_coords = detected_hands[1]

        direct_distance = (
            landmark_xy_distance(first_hand, pose_landmarks[LEFT_WRIST_POSE_INDEX])
            + landmark_xy_distance(second_hand, pose_landmarks[RIGHT_WRIST_POSE_INDEX])
        )
        swapped_distance = (
            landmark_xy_distance(first_hand, pose_landmarks[RIGHT_WRIST_POSE_INDEX])
            + landmark_xy_distance(second_hand, pose_landmarks[LEFT_WRIST_POSE_INDEX])
        )

        if direct_distance <= swapped_distance:
            left_hand = first_coords
            right_hand = second_coords
        else:
            left_hand = second_coords
            right_hand = first_coords

    else:
        for _, label, coords in detected_hands:
            if label == "Right":
                left_hand = coords
            else:
                right_hand = coords

    features.extend(left_hand if left_hand is not None else [np.nan] * 63)
    features.extend(right_hand if right_hand is not None else [np.nan] * 63)

    if len(features) != FEATURE_SIZE:
        raise ValueError(f"Invalid feature vector size: {len(features)}")

    return np.array(features, dtype=np.float32)


def process_video(video_path: Path, hands, pose, timestamp_offset_ms: int):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None, timestamp_offset_ms

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_index = 0
    sequence = []

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            timestamp_ms = timestamp_offset_ms + int(frame_index * 1000 / fps)

            hands_result = hands.detect_for_video(image, timestamp_ms)
            pose_result = pose.detect_for_video(image, timestamp_ms)

            sequence.append(extract_landmarks(hands_result, pose_result))
            frame_index += 1
    finally:
        cap.release()

    next_timestamp_offset_ms = timestamp_offset_ms + int((frame_index + 1) * 1000 / fps)

    if not sequence:
        return None, next_timestamp_offset_ms

    return np.array(sequence, dtype=np.float32), next_timestamp_offset_ms


# --- Sequence preprocessing -------------------------------------------------
# Must match research/test_version/DataProcessing/preprocessing.py exactly:
# it is applied identically to training data and to inference input.

LEFT_SHOULDER = slice(0, 3)
RIGHT_SHOULDER = slice(3, 6)
LEFT_WRIST = slice(12, 15)
RIGHT_WRIST = slice(15, 18)

LEFT_HAND = slice(18, 81)
RIGHT_HAND = slice(81, 144)


def hands_activity(sequence: np.ndarray, threshold=0.15) -> np.ndarray:
    seq = sequence.copy()
    num_frames = len(seq)

    left_nan_frames = np.isnan(seq[:, LEFT_HAND]).all(axis=1)
    right_nan_frames = np.isnan(seq[:, RIGHT_HAND]).all(axis=1)

    left_valid_ratio = 1.0 - left_nan_frames.mean()
    right_valid_ratio = 1.0 - right_nan_frames.mean()

    if left_valid_ratio < threshold:
        for frame in range(num_frames):
            shoulder_pos = seq[frame, LEFT_SHOULDER]
            if np.isnan(shoulder_pos).any():
                shoulder_pos = np.zeros(3)
            seq[frame, LEFT_HAND] = np.tile(shoulder_pos, 21)

    if right_valid_ratio < threshold:
        for frame in range(num_frames):
            shoulder_pos = seq[frame, RIGHT_SHOULDER]
            if np.isnan(shoulder_pos).any():
                shoulder_pos = np.zeros(3)
            seq[frame, RIGHT_HAND] = np.tile(shoulder_pos, 21)

    return seq


def interpolate_position(sequence: np.ndarray) -> np.ndarray:
    seq = sequence.copy()
    num_frames = len(seq)
    indices = np.arange(num_frames)

    for dim in range(seq.shape[1]):
        col = seq[:, dim]
        nan_mask = np.isnan(col)

        if nan_mask.all():
            seq[:, dim] = 0.0
            continue

        if not nan_mask.any():
            continue

        valid_idx = indices[~nan_mask]
        valid_vals = col[~nan_mask]

        seq[:, dim] = np.interp(indices, valid_idx, valid_vals, left=valid_vals[0], right=valid_vals[-1])

    return seq


def remove_static_frames(sequence: np.ndarray, threshold=0.01) -> np.ndarray:
    frame_differences = np.diff(sequence, axis=0)
    motion_magnitude = np.linalg.norm(frame_differences, axis=1)

    dynamic_idx = np.where(motion_magnitude > threshold)[0]

    if len(dynamic_idx) < 10:
        return sequence

    return sequence[dynamic_idx]


def savitzky_golay_filter(sequence: np.ndarray, window_length=5, polyorder=2) -> np.ndarray:
    if len(sequence) < window_length:
        return sequence

    return savgol_filter(sequence, window_length=window_length, polyorder=polyorder, axis=0)


def normalization(sequence: np.ndarray) -> np.ndarray:
    normalized = sequence.copy().astype(np.float32)

    left_sh = normalized[:, LEFT_SHOULDER]
    right_sh = normalized[:, RIGHT_SHOULDER]
    center = (left_sh + right_sh) / 2.0

    for i in range(0, normalized.shape[1], 3):
        normalized[:, i:i + 3] -= center

    shoulder_dist = normalized[:, LEFT_SHOULDER] - normalized[:, RIGHT_SHOULDER]
    scale_factor = np.linalg.norm(shoulder_dist, axis=1, keepdims=True) + 1e-6

    normalized /= np.repeat(scale_factor, normalized.shape[1], axis=1)

    return normalized


def resample_sequence(sequence: np.ndarray, target_len=60) -> np.ndarray:
    num_frames, num_features = sequence.shape

    if num_frames == target_len:
        return sequence

    original_timestamps = np.linspace(0, 1, num_frames)
    target_timestamps = np.linspace(0, 1, target_len)

    resampled = np.zeros((target_len, num_features), dtype=np.float32)

    for feature_idx in range(num_features):
        interpolation_fn = interp1d(original_timestamps, sequence[:, feature_idx], kind="linear")
        resampled[:, feature_idx] = interpolation_fn(target_timestamps)

    return resampled


def preprocess(sequence: np.ndarray, target_len=60) -> np.ndarray:
    seq = hands_activity(sequence)
    seq = interpolate_position(seq)
    seq = remove_static_frames(seq)
    seq = savitzky_golay_filter(seq)
    seq = normalization(seq)
    seq = resample_sequence(seq, target_len)
    return seq
