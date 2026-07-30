import csv
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
import cv2
import numpy as np
import torch
import torch.nn as nn
from DataProcessing.preprocessing import preprocess
from Recognition.faiss_dtw import faiss_search

class SegmenterState(Enum):
    IDLE = auto()
    RECORDING = auto()


@dataclass
class GestureSegmenter:
    activity_start_frames: int = 3
    activity_end_frames: int = 10
    max_buffer_frames: int = 150
    min_gesture_frames: int = 8
    state: SegmenterState = SegmenterState.IDLE
    active_streak: int = 0
    inactive_streak: int = 0
    buffer: deque = field(init=False)

    def __post_init__(self):
        self.buffer = deque(maxlen=self.max_buffer_frames)

    def update(self, feature_vector: np.ndarray, hand_detected: bool) -> np.ndarray | None:
        if hand_detected:
            self.active_streak += 1
            self.inactive_streak = 0
        else:
            self.inactive_streak += 1
            self.active_streak = 0

        if self.state == SegmenterState.IDLE:
            if self.active_streak >= self.activity_start_frames:
                self.state = SegmenterState.RECORDING
                self.buffer.clear()
                self.buffer.append(feature_vector)
            return None

        # state == RECORDING
        self.buffer.append(feature_vector)

        if self.inactive_streak >= self.activity_end_frames or len(self.buffer) >= self.max_buffer_frames:
            self.state = SegmenterState.IDLE
            sequence = np.array(self.buffer, dtype=np.float32)
            self.buffer.clear()
            self.active_streak = 0
            self.inactive_streak = 0
            return sequence if sequence.shape[0] >= self.min_gesture_frames else None

        return None


@dataclass
class EncoderBundle:
    model: nn.Module
    label_map: dict
    normalize_embeddings: bool


def load_encoder(checkpoint_path: Path, model: nn.Module, device: str) -> EncoderBundle:
    checkpoint = torch.load(checkpoint_path, map_location=device)
    config = checkpoint["config"]
    model = model(
        input_dim=config["input_dim"],
        hidden_dim=config["hidden_dim"],
        num_layers=config["num_layers"],
        dropout=config["dropout"],
    )
    model.load_state_dict(checkpoint["model_state"])
    model.to(device)
    model.eval()

    return EncoderBundle(
        model=model,
        label_map=checkpoint["label_map"],
        normalize_embeddings=config.get("normalize_embeddings", False),
    )


@torch.no_grad()
def embed_sequence(bundle: EncoderBundle, preprocessed_sequence: np.ndarray, device: str) -> np.ndarray:
    x = torch.tensor(preprocessed_sequence, dtype=torch.float32, device=device).unsqueeze(0)  # [1, 60, 144]
    embedding, _ = bundle.model(x)

    if bundle.normalize_embeddings:
        embedding = torch.nn.functional.normalize(embedding, p=2, dim=1)

    return embedding.cpu().numpy()


def recognize_gesture(embedding: np.ndarray, faiss_index, train_labels, id_to_label, k: int) -> str:
    candidate_indices = faiss_search(faiss_index, embedding.reshape(-1), k)
    predicted_label_id = train_labels[candidate_indices[0]]
    return str(id_to_label[predicted_label_id])


def try_recognize(raw_sequence, encoder_bundle, faiss_index, train_labels, id_to_label, device, target_len, k=1):
    try:
        processed = preprocess(raw_sequence, target_len=target_len)
        embedding = embed_sequence(encoder_bundle, processed, device=device)
        return recognize_gesture(embedding, faiss_index, train_labels, id_to_label, k=k)
    except Exception as exc:
        print(f"Error processing: {exc}")
        return None


def draw_hands(frame, hand_result, hand_connections):
    if not hand_result.hand_landmarks:
        return

    h, w = frame.shape[:2]
    for hand_landmarks in hand_result.hand_landmarks:
        points = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks]
        for start_idx, end_idx in hand_connections:
            cv2.line(frame, points[start_idx], points[end_idx], (255, 200, 0), 2)
        for x, y in points:
            cv2.circle(frame, (x, y), 3, (0, 140, 255), -1)


def draw_pose(frame, pose_result, pose_key_points, pose_connections):
    if not pose_result.pose_landmarks:
        return

    h, w = frame.shape[:2]
    landmarks = pose_result.pose_landmarks[0]  # num_poses=1
    points = {idx: (int(landmarks[idx].x * w), int(landmarks[idx].y * h)) for idx in pose_key_points}

    for start_idx, end_idx in pose_connections:
        cv2.line(frame, points[start_idx], points[end_idx], (0, 200, 0), 2)
    for x, y in points.values():
        cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)


def diagnostic_prompt(frame, true_label, trial_index, total_trials, status, last_prediction):
    cv2.putText(frame, f"Trial {trial_index}/{total_trials}  SHOW: {true_label}", (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 3)
    cv2.putText(frame, f"Status: {status}   Last prediction: {last_prediction or '-'}", (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    cv2.putText(frame, "Make the gesture, then pause. Q quits.", (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)


def recognition_prompt(frame, status, last_prediction, sentence_memory):
    cv2.putText(frame, f"Status: {status}", (10, 640), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
    cv2.putText(frame, f"Gesture: {last_prediction}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
    sentence_text = " ".join(sentence_memory) if sentence_memory else "(empty)"
    cv2.putText(frame, f"Sentence: {sentence_text}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (220, 220, 0), 2)
    cv2.putText(frame, "[R] Reset sentence [E] Erase last word [Q] Quit", (10, 680), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)


@dataclass
class DiagnosticTrial:
    trial: int
    true_label: str
    predicted_label: str

    @property
    def correct(self) -> bool:
        return self.predicted_label == self.true_label

