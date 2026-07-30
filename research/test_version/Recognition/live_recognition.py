import csv
import random
import time
from pathlib import Path
import cv2
import numpy as np
import mediapipe as mp
import torch
from DataProcessing.collector import create_landmarkers, extract_landmarks, POSE_KEY_POINTS
from Recognition.faiss_dtw import load_faiss_index
from Recognition.recognition_utils import (
    GestureSegmenter,
    SegmenterState,
    load_encoder,
    try_recognize,
    draw_hands,
    draw_pose,
    recognition_prompt,
    diagnostic_prompt,
)
from Models.Transformer_encoder import TransformerEncoder

# --- LIVE (segmenter, for gestures WITH pauses) ---
ACTIVITY_START_FRAMES = 5
ACTIVITY_END_FRAMES = 10
MAX_BUFFER_FRAMES = 150
MIN_GESTURE_FRAMES = 8
TARGET_LEN = 60

# --- MODEL ENCODER ---
MODEL = TransformerEncoder
MODEL_CHECKPOINT_PATH = Path(f"Models/{MODEL.__name__}_Checkpoints/best_encoder.pt")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# --- FAISS ---
FAISS_TOP_K = 1

PREDICTION_DISPLAY_SECONDS = 3.0

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]
POSE_CONNECTIONS = [(11, 13), (13, 15), (12, 14), (14, 16)]

CAPTURE_WIDTH = 1280
CAPTURE_HEIGHT = 720
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720


def run_live_recognition(
    is_diagnostic: bool = False,
    is_custom_database: bool = True,
    labels: list[str] | None = None,
    repeats: int = 3,
    shuffle: bool = True,
    camera_index: int = 0,
    top_k: int = 1,
    checkpoint_path: str | Path = MODEL_CHECKPOINT_PATH,
) -> dict[str, list] | None:
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"ERROR: Camera {camera_index} not found")
        return None

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAPTURE_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAPTURE_HEIGHT)

    window_name = "LIVE DIAGNOSTIC" if is_diagnostic else "CAMERA FEED"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, WINDOW_WIDTH, WINDOW_HEIGHT)

    hand_landmarker, pose_landmarker = create_landmarkers()
    encoder_bundle = load_encoder(Path(checkpoint_path), MODEL, DEVICE)
    print(f"Model works on: {DEVICE}")

    faiss_index_path = f"Recognition/{MODEL.__name__}_db_{'custom' if is_custom_database else 'base'}/index.faiss"
    faiss_labels_path = f"Recognition/{MODEL.__name__}_db_{'custom' if is_custom_database else 'base'}/index_labels.npz"
    
    faiss_index = load_faiss_index(faiss_index_path)
    labels_data = np.load(faiss_labels_path, allow_pickle=True)

    db_labels = labels_data["labels"]
    id_to_label = labels_data["id_to_label"]
    print(f"FAISS index: {faiss_index.ntotal} vectors, {len(id_to_label)} gesture classes")

    trial_labels: list[str] = []
    if is_diagnostic:
        pool = [str(l) for l in (labels if labels is not None else id_to_label)]
        trial_labels = [label for label in pool for _ in range(repeats)]
        if shuffle:
            random.shuffle(trial_labels)

    results: dict[str, list] = {
        "trial": [],
        "true_label": [],
        "predicted_label": [],
        "correct": [],
    }
    sentence_memory: list[str] = []
    last_prediction = ""
    last_prediction_time = 0.0
    trial_idx = 0
    segmenter = GestureSegmenter(ACTIVITY_START_FRAMES, ACTIVITY_END_FRAMES, MAX_BUFFER_FRAMES, MIN_GESTURE_FRAMES)
    start_time = time.time()

    try:
        while True:
            if is_diagnostic and trial_idx >= len(trial_labels):
                break

            ok, frame = cap.read()
            if not ok:
                print("ERROR: Failed to get frame")
                break
            
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            timestamp_ms = int((time.time() - start_time) * 1000)

            hand_result = hand_landmarker.detect_for_video(mp_image, timestamp_ms)
            pose_result = pose_landmarker.detect_for_video(mp_image, timestamp_ms)
            feature_vector = extract_landmarks(hand_result, pose_result)
            
            left_missing = np.isnan(feature_vector[18:81]).any()
            right_missing = np.isnan(feature_vector[81:144]).any()
            hand_detected = not (left_missing and right_missing)

            raw_sequence = segmenter.update(feature_vector, hand_detected)
            if raw_sequence is not None:
                predicted = try_recognize(
                    raw_sequence, encoder_bundle, faiss_index, db_labels, id_to_label, DEVICE, TARGET_LEN, top_k
                )
                if predicted is not None:
                    last_prediction = predicted
                    last_prediction_time = time.time()

                    if is_diagnostic:
                        true_label = trial_labels[trial_idx]
                        results["trial"].append(trial_idx + 1)
                        results["true_label"].append(true_label)
                        results["predicted_label"].append(predicted)
                        results["correct"].append(predicted == true_label)
                        print(f"[{trial_idx + 1}/{len(trial_labels)}] true={true_label} pred={predicted} correct={predicted == true_label}")
                        trial_idx += 1
                    else:
                        sentence_memory.append(predicted)

            draw_pose(frame, pose_result, POSE_KEY_POINTS, POSE_CONNECTIONS)
            draw_hands(frame, hand_result, HAND_CONNECTIONS)
            status = "RECORDING" if segmenter.state == SegmenterState.RECORDING else "IDLE"

            if is_diagnostic:
                true_label = trial_labels[trial_idx] if trial_idx < len(trial_labels) else "-"
                diagnostic_prompt(frame, true_label, trial_idx + 1, len(trial_labels), status, last_prediction)
            else:
                fresh = bool(last_prediction) and (time.time() - last_prediction_time) < PREDICTION_DISPLAY_SECONDS
                recognition_prompt(frame, status, last_prediction if fresh else "None", sentence_memory)

            cv2.imshow(window_name, frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if not is_diagnostic:
                if key == ord("r"):
                    sentence_memory.clear()
                elif key == ord("e"):
                    sentence_memory = sentence_memory[:-1]

    except KeyboardInterrupt:
        print("Stopped by user.")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        hand_landmarker.close()
        pose_landmarker.close()

    if is_diagnostic:
        total = len(results["correct"])
        if total == 0:
            print("No diagnostic trials were recorded.")
        else:
            correct_count = sum(results["correct"])
            print(f"Accuracy: {correct_count / total:.2%} ({correct_count}/{total})")

        return results

    return None


if __name__ == "__main__":
    run_live_recognition()
