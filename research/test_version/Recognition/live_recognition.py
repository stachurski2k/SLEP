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
    SlidingWindowRecognizer,
    load_encoder,
    draw_hands,
    draw_pose,
    recognition_prompt,
    diagnostic_prompt,
)

from Models.Transformer_encoder import TransformerEncoder
from Models.LSTM_encoder import LSTMEncoder
from Models.BiLSTM_encoder import BiLSTMEncoder
from Models.GRU_encoder import GRUEncoder
from Models.BiGRU_encoder import BiGRUEncoder

MODEL_REGISTRY: dict[str, type] = {
    "Transformer": TransformerEncoder,
    "LSTM": LSTMEncoder,
    "BiLSTM": BiLSTMEncoder,
    "GRU": GRUEncoder,
    "BiGRU": BiGRUEncoder,
}

# --- LIVE (segmenter, for gestures WITH pauses) ---
ACTIVITY_START_FRAMES = 3
ACTIVITY_END_FRAMES = 10
MAX_BUFFER_FRAMES = 150
MIN_GESTURE_FRAMES = 8
TARGET_LEN = 60

# --- LIVE (sliding window, for smooth gesture streams) ---
SLIDING_ACTIVITY_START_FRAMES = 1
SLIDING_ACTIVITY_END_FRAMES   = 3
SLIDING_WINDOW_FRAMES         = 5
SLIDING_STEP_FRAMES           = 2
SLIDING_STABILITY_WINDOW      = 3
SLIDING_REQUIRED_VOTES        = 2
SLIDING_SWITCH_REQUIRED_VOTES = 3
SLIDING_COOLDOWN_FRAMES       = 3
SLIDING_MIN_HAND_RATIO        = 0.6
SLIDING_MIN_SCORE             = 0.75
SLIDING_MIN_MARGIN            = 0.03
SLIDING_CUSTOM_MIN_SCORE      = 0.1
SLIDING_CUSTOM_MIN_MARGIN     = 0.03


# --- MODEL ENCODER ---
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

def release_resources(cap, hand_landmarker, pose_landmarker):
    cap.release()
    cv2.destroyAllWindows()
    hand_landmarker.close()
    pose_landmarker.close()

def run_live_recognition(
    is_diagnostic: bool = False,
    is_custom_database: bool = True,
    is_sliding_window: bool = False,
    labels: list[str] | None = None,
    repeats: int = 3,
    shuffle: bool = True,
    camera_index: int = 0,
    top_k: int = 1,
    model: str | None = None
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

    if model is None:
        model = "Transformer"

    model_cls = MODEL_REGISTRY.get(model)
    if model_cls is None:
        print(f"ERROR: Unknown model '{model}'. Available: {list(MODEL_REGISTRY)}")
        release_resources(cap, hand_landmarker, pose_landmarker)
        return None

    model_checkpoint_path = Path(f"Models/{model}Encoder_Checkpoints/best_encoder.pt")
    faiss_index_path = Path(f"Recognition/{model}Encoder_db_{'custom' if is_custom_database else 'base'}/index.faiss")
    faiss_labels_path = Path(f"Recognition/{model}Encoder_db_{'custom' if is_custom_database else 'base'}/index_labels.npz")
    
    if model_checkpoint_path.exists() == False:
        print(f"ERROR: Model checkpoint not found at {model_checkpoint_path}")
        release_resources(cap, hand_landmarker, pose_landmarker)
        return None

    if faiss_index_path.exists() == False:
        print(f"ERROR: FAISS index not found at {faiss_index_path}")
        release_resources(cap, hand_landmarker, pose_landmarker)
        return None

    if faiss_labels_path.exists() == False:
        print(f"ERROR: FAISS labels not found at {faiss_labels_path}")
        release_resources(cap, hand_landmarker, pose_landmarker)
        return None

    encoder_bundle = load_encoder(model_checkpoint_path, model_cls, DEVICE)
    print(f"Model works on: {DEVICE}")

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
        "score": [],
        "margin": [],
    }
    sentence_memory: list[str] = []
    last_prediction = ""
    last_prediction_details = ""
    last_prediction_time = 0.0
    trial_idx = 0

    segmenter = GestureSegmenter(
        encoder_bundle=encoder_bundle,
        faiss_index=faiss_index,
        train_labels=db_labels,
        id_to_label=id_to_label,
        device=DEVICE,
        activity_start_frames=ACTIVITY_START_FRAMES,
        activity_end_frames=ACTIVITY_END_FRAMES,
        max_buffer_frames=MAX_BUFFER_FRAMES,
        min_gesture_frames=MIN_GESTURE_FRAMES,
        target_len=TARGET_LEN,
        top_k=top_k,
    )
    sliding_recognizer = SlidingWindowRecognizer(
        encoder_bundle=encoder_bundle,
        faiss_index=faiss_index,
        train_labels=db_labels,
        id_to_label=id_to_label,
        device=DEVICE,
        activity_start_frames=SLIDING_ACTIVITY_START_FRAMES,
        activity_end_frames=SLIDING_ACTIVITY_END_FRAMES,
        target_len=TARGET_LEN,
        top_k=max(5, top_k),

        window_frames=SLIDING_WINDOW_FRAMES,
        step_frames=SLIDING_STEP_FRAMES,
        min_score=SLIDING_MIN_SCORE,
        min_margin=SLIDING_MIN_MARGIN,
        custom_min_score=SLIDING_CUSTOM_MIN_SCORE,
        custom_min_margin=SLIDING_CUSTOM_MIN_MARGIN,
        stability_window=SLIDING_STABILITY_WINDOW,
        required_votes=SLIDING_REQUIRED_VOTES,
        cooldown_frames=SLIDING_COOLDOWN_FRAMES,
        min_hand_ratio=SLIDING_MIN_HAND_RATIO,
        switch_required_votes=SLIDING_SWITCH_REQUIRED_VOTES,
        is_custom_database=is_custom_database,
    )
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

            hand_detected = bool(hand_result.hand_landmarks)

            active_recognizer = sliding_recognizer if is_sliding_window else segmenter
            result = active_recognizer.update(feature_vector, hand_detected)

            predicted = result.label if result is not None else None

            if predicted is not None:
                last_prediction = predicted
                last_prediction_details = f"{result.label} score={result.score:.2f} margin={result.margin:.2f}"
                last_prediction_time = time.time()

                if is_diagnostic:
                    true_label = trial_labels[trial_idx]
                    results["trial"].append(trial_idx + 1)
                    results["true_label"].append(true_label)
                    results["predicted_label"].append(predicted)
                    results["correct"].append(predicted == true_label)
                    results["score"].append(result.score)
                    results["margin"].append(result.margin)
                    print(f"[{trial_idx + 1}/{len(trial_labels)}] true={true_label} pred={predicted} correct={predicted == true_label} score={result.score:.2f} margin={result.margin:.2f}")
                    trial_idx += 1
                else:
                    sentence_memory.append(predicted)

            draw_pose(frame, pose_result, POSE_KEY_POINTS, POSE_CONNECTIONS)
            draw_hands(frame, hand_result, HAND_CONNECTIONS)
            status = active_recognizer.status

            if is_diagnostic:
                true_label = trial_labels[trial_idx] if trial_idx < len(trial_labels) else "-"
                diagnostic_prompt(frame, true_label, trial_idx + 1, len(trial_labels), status, last_prediction)
            else:
                fresh = bool(last_prediction) and (time.time() - last_prediction_time) < PREDICTION_DISPLAY_SECONDS
                recognition_prompt(frame, status, last_prediction_details if fresh else "None", sentence_memory)

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
        release_resources(cap, hand_landmarker, pose_landmarker)

    if is_diagnostic:
        total = len(results["correct"])
        if total == 0:
            print("No diagnostic trials were recorded.")
        else:
            correct_count = sum(results["correct"])
            print(f"Accuracy: {correct_count / total:.2%} ({correct_count}/{total})")
            avg_total_score = sum(results["score"])/total
            print(f"Average Total Score: {avg_total_score:.2f}")
            avg_total_margin = sum(results["margin"])/total
            print(f"Average Total Margin: {avg_total_margin:.2f}")
        return results

    return None


if __name__ == "__main__":
    run_live_recognition()
