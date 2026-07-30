import os
from pathlib import Path
os.environ["TF_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["GLOG_minloglevel"] = "2"
os.environ["ABSL_LOGGING_MIN_LEVEL"] = "2"

import cv2
import mediapipe as mp
import numpy as np
from tqdm import tqdm

try:
    from absl import logging as absl_logging

    absl_logging.set_verbosity(absl_logging.ERROR)
except ImportError:
    pass


DATASET_DIR = Path("Dataset")
OUTPUT_DIR = Path("Features")
MODELS_DIR = Path("MediapipeModels")

HAND_MODEL_PATH = MODELS_DIR / "hand_landmarker.task"
POSE_MODEL_PATH = MODELS_DIR / "pose_landmarker_full.task"

POSE_KEY_POINTS = [11, 12, 13, 14, 15, 16]
LEFT_WRIST_POSE_INDEX = 15
RIGHT_WRIST_POSE_INDEX = 16
FEATURE_SIZE = 144


BaseOptions = mp.tasks.BaseOptions
RunningMode = mp.tasks.vision.RunningMode

HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions

PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions


def create_landmarkers():
    hands_options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(HAND_MODEL_PATH)),
        running_mode=RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.25,
        min_hand_presence_confidence=0.25,
        min_tracking_confidence=0.3,
    )

    pose_options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(POSE_MODEL_PATH)),
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
        print(f"  Cannot open video: {video_path}")
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


def collect_landmarks(dataset_dir: Path = DATASET_DIR, output_dir: Path = OUTPUT_DIR):
    output_dir.mkdir(exist_ok=True)
    gesture_dirs = sorted(d for d in dataset_dir.iterdir() if d.is_dir())

    hands, pose = create_landmarkers()
    timestamp_offset_ms = 0

    try:
        for gesture_dir in gesture_dirs:
            gesture_name = gesture_dir.name
            output_gesture_dir = output_dir / gesture_name
            output_gesture_dir.mkdir(exist_ok=True)

            video_files = sorted(gesture_dir.glob("*.mp4"))
            print(f"\nProcessing gesture: {gesture_name} ({len(video_files)} files)")

            for video_path in tqdm(video_files):
                sequence, timestamp_offset_ms = process_video(
                    video_path,
                    hands,
                    pose,
                    timestamp_offset_ms,
                )
                if sequence is None:
                    print(f"  Empty video: {video_path.name}")
                    continue

                output_path = output_gesture_dir / f"{video_path.stem}.npy"
                np.save(output_path, sequence)

                pose_nan_ratio = np.isnan(sequence[:, 0:18]).any(axis=1).mean()
                left_nan_ratio = np.isnan(sequence[:, 18:81]).any(axis=1).mean()
                right_nan_ratio = np.isnan(sequence[:, 81:144]).any(axis=1).mean()

                #if max(pose_nan_ratio, left_nan_ratio, right_nan_ratio) > 0.5:
                print(
                        f"  {video_path.name}: "
                        f"pose {pose_nan_ratio:.0%}, "
                        f"left {left_nan_ratio:.0%}, "
                        f"right {right_nan_ratio:.0%} lost"
                    )
    finally:
        hands.close()
        pose.close()


if __name__ == "__main__":
    collect_landmarks()
    print("-" * 60)
    print(f"Landmark extraction finished and saved in {OUTPUT_DIR}")
    print("-" * 60)
