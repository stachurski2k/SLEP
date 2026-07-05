import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
import cv2
import numpy as np
import mediapipe as mp
import torch
import torch.nn as nn
from DataProcessing.collector import (
    create_landmarkers,
    enhance_frame,
    extract_landmarks,
    POSE_KEY_POINTS,
)
from DataProcessing.preprocessing import preprocess
from Models.LSTM_encoder import LSTMEncoder
from Models.Transformer_encoder import TransformerEncoder
from Recognition.faiss_dtw import load_faiss_index, faiss_search, dtw_decider

# --- LIVE ---
ACTIVITY_START_FRAMES = 3     # frames with hand to start recording
ACTIVITY_END_FRAMES = 10      # frames without hand to end recording
MAX_BUFFER_FRAMES = 150       # buffer size
MIN_GESTURE_FRAMES = 8        # min frames to be counted as a gesture
TARGET_LEN = 60               # target length of a sequence


# --- model encodera ---
MODEL = TransformerEncoder
MODEL_CHECKPOINT_PATH = Path(f"Models/{MODEL.__name__}_Checkpoints/best_encoder.pt")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# --- baza FAISS -- tylko wczytywanie, budowana osobno przez Recognition/build_index.py ---
FAISS_INDEX_PATH = f"Recognition/{MODEL.__name__}_db/index.faiss"
FAISS_LABELS_PATH = f"Recognition/{MODEL.__name__}_db/index_labels.npz"
FAISS_TOP_K = 1  # k=1 -> najbliższy sąsiad; zwiększ jeśli dodasz rerank przez DTW

# jak długo trzymać ostatni wynik rozpoznania na ekranie
PREDICTION_DISPLAY_SECONDS = 3.0

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),          # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),          # index finger
    (5, 9), (9, 10), (10, 11), (11, 12),     # middle finger
    (9, 13), (13, 14), (14, 15), (15, 16),   # ring finger
    (13, 17), (17, 18), (18, 19), (19, 20),  # pinky
    (0, 17),                                 # wrist -> pinky base
]

# shoulder -> elbow -> wrist
POSE_CONNECTIONS = [(11, 13), (13, 15), (12, 14), (14, 16)]

# resolution
CAPTURE_WIDTH = 1280
CAPTURE_HEIGHT = 720

# window size
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720


class SegmenterState(Enum):
    IDLE = auto()
    RECORDING = auto()


@dataclass
class GestureSegmenter:
    state: SegmenterState = SegmenterState.IDLE
    active_streak: int = 0
    inactive_streak: int = 0
    buffer: deque = field(default_factory=lambda: deque(maxlen=MAX_BUFFER_FRAMES))

    def update(self, feature_vector: np.ndarray, hand_detected: bool) -> np.ndarray | None:
        if hand_detected:
            self.active_streak += 1
            self.inactive_streak = 0
        else:
            self.inactive_streak += 1
            self.active_streak = 0

        if self.state == SegmenterState.IDLE:
            if self.active_streak >= ACTIVITY_START_FRAMES:
                self.state = SegmenterState.RECORDING
                self.buffer.clear()
                self.buffer.append(feature_vector)
            return None

        # state == RECORDING
        self.buffer.append(feature_vector)

        if self.inactive_streak >= ACTIVITY_END_FRAMES or len(self.buffer) >= MAX_BUFFER_FRAMES:
            self.state = SegmenterState.IDLE
            sequence = np.array(self.buffer, dtype=np.float32)
            self.buffer.clear()
            self.active_streak = 0
            self.inactive_streak = 0

            if sequence.shape[0] < MIN_GESTURE_FRAMES:
                return None
            return sequence

        return None


@dataclass
class EncoderBundle:
    model: nn.Module
    label_map: dict
    normalize_embeddings: bool


def load_encoder(checkpoint_path: Path) -> EncoderBundle:
    checkpoint = torch.load(checkpoint_path, map_location=DEVICE)

    config = checkpoint["config"]
    model = MODEL(
        input_dim=config["input_dim"],
        hidden_dim=config["hidden_dim"],
        num_layers=config["num_layers"],
        dropout=config["dropout"],
    )
    model.load_state_dict(checkpoint["model_state"])
    model.to(DEVICE)
    model.eval()

    return EncoderBundle(
        model=model,
        label_map=checkpoint["label_map"],
        normalize_embeddings=config.get("normalize_embeddings", False),
    )


@torch.no_grad()
def embed_sequence(bundle: EncoderBundle, preprocessed_sequence: np.ndarray) -> np.ndarray:
    x = torch.tensor(preprocessed_sequence, dtype=torch.float32, device=DEVICE).unsqueeze(0)  # [1, 60, 144]
    embedding, reconstructed = bundle.model(x)

    if bundle.normalize_embeddings:
        embedding = torch.nn.functional.normalize(embedding, dim=0)

    return embedding.cpu().numpy()


def recognize_gesture(embedding: np.ndarray, faiss_index, train_labels, id_to_label) -> str:
    candidate_indices = faiss_search(faiss_index, embedding.reshape(-1), k=FAISS_TOP_K)
    predicted_label_id = train_labels[candidate_indices[0]]
    return str(id_to_label[predicted_label_id])


def draw_hands(frame, hand_result):
    if not hand_result.hand_landmarks:
        return

    h, w = frame.shape[:2]
    for hand_landmarks in hand_result.hand_landmarks:
        points = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks]

        for start_idx, end_idx in HAND_CONNECTIONS:
            cv2.line(frame, points[start_idx], points[end_idx], (255, 200, 0), 2)

        for x, y in points:
            cv2.circle(frame, (x, y), 3, (0, 140, 255), -1)


def draw_pose(frame, pose_result):
    if not pose_result.pose_landmarks:
        return

    h, w = frame.shape[:2]
    landmarks = pose_result.pose_landmarks[0]  # num_poses=1

    points = {idx: (int(landmarks[idx].x * w), int(landmarks[idx].y * h)) for idx in POSE_KEY_POINTS}

    for start_idx, end_idx in POSE_CONNECTIONS:
        cv2.line(frame, points[start_idx], points[end_idx], (0, 200, 0), 2)

    for x, y in points.values():
        cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Camera not found")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAPTURE_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAPTURE_HEIGHT)

    actual_w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    actual_h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print(f"Camera resolution: {int(actual_w)}x{int(actual_h)}")

    window_name = "CAMERA FEED"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, WINDOW_WIDTH, WINDOW_HEIGHT)

    hand_landmarker, pose_landmarker = create_landmarkers()
    segmenter = GestureSegmenter()

    encoder_bundle = load_encoder(MODEL_CHECKPOINT_PATH)
    print(f"Model works on: {DEVICE}")

    faiss_index = load_faiss_index(FAISS_INDEX_PATH)
    labels_data = np.load(FAISS_LABELS_PATH)
    train_labels = labels_data["labels"]
    id_to_label = labels_data["id_to_label"]
    print(f"FAISS index: {faiss_index.ntotal} vectors, {len(id_to_label)} gesture classes")

    last_prediction = ""
    last_prediction_time = 0.0

    start_time = time.time()

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("ERROR: Failed to get frame")
                break

            frame = enhance_frame(frame)

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            timestamp_ms = int((time.time() - start_time) * 1000)

            hand_result = hand_landmarker.detect_for_video(mp_image, timestamp_ms)
            pose_result = pose_landmarker.detect_for_video(mp_image, timestamp_ms)

            feature_vector = extract_landmarks(hand_result, pose_result)

            pose_missing = np.isnan(feature_vector[0:18]).any()
            left_missing = np.isnan(feature_vector[18:81]).any()
            right_missing = np.isnan(feature_vector[81:144]).any()
            hand_detected = not (left_missing and right_missing)

            detection_text = (
                f"POSE: {'MISSING' if pose_missing else 'OK'}  "
                f"LEFT HAND: {'MISSING' if left_missing else 'OK'}  "
                f"RIGHT HAND: {'MISSING' if right_missing else 'OK'}"
            )

            # --- segmentation ---
            raw_sequence = segmenter.update(feature_vector, hand_detected)
            if raw_sequence is not None:
                print(f"Raw sequence shape: {raw_sequence.shape}")
                try:
                    processed_sequence = preprocess(raw_sequence, target_len=TARGET_LEN)
                    print(f"Processed sequence shape: {processed_sequence.shape}")

                    embedding = embed_sequence(encoder_bundle, processed_sequence)
                    print(f"Embedding: shape={embedding.shape}, norm={np.linalg.norm(embedding):.3f}")

                    predicted_label = recognize_gesture(embedding, faiss_index, train_labels, id_to_label)
                    print(f"Recognized gesture: {predicted_label}")

                    last_prediction = predicted_label
                    last_prediction_time = time.time()
                except Exception as exc:
                    print(f"Error processing: {exc}")

            # rysowanie -- TYLKO RAZ na klatkę
            draw_pose(frame, pose_result)
            draw_hands(frame, hand_result)

            status = "RECORDING" if segmenter.state == SegmenterState.RECORDING else "IDLE"
            cv2.putText(frame, f"Status: {status}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

            if last_prediction and (time.time() - last_prediction_time) < PREDICTION_DISPLAY_SECONDS:
                gesture_text = last_prediction
            else:
                gesture_text = "None"
            
            cv2.putText(frame, f"Gesture: {gesture_text}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 220, 0), 3)

            cv2.putText(frame, f"{detection_text}", (10, 1050), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)

            cv2.imshow(window_name, frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        hand_landmarker.close()
        pose_landmarker.close()


if __name__ == "__main__":
    main()