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


class RecognizerState(Enum):
    WAITING = auto()
    RECORDING = auto()


@dataclass
class EncoderBundle:
    model: nn.Module
    label_map: dict
    normalize_embeddings: bool


@dataclass
class RecognitionResult:
    label: str
    score: float
    margin: float


def load_encoder(checkpoint_path: Path, model_cls: type[nn.Module], device: str) -> EncoderBundle:
    checkpoint = torch.load(checkpoint_path, map_location=device)
    config = checkpoint["config"]
    model = model_cls(
        input_dim=config["input_dim"],
        hidden_dim=config["hidden_dim"],
        num_layers=config["num_layers"],
        dropout=config["dropout"],
    )
    model.load_state_dict(checkpoint["model_state"])
    model.to(device)
    model.eval()

    with torch.no_grad():
        dummy = torch.zeros(1, config.get("target_len", 60), config["input_dim"], device=device)
        model(dummy)

    return EncoderBundle(
        model=model,
        label_map=checkpoint["label_map"],
        normalize_embeddings=config.get("normalize_embeddings", False),
    )


@torch.no_grad()
def embed_sequence(bundle: EncoderBundle, preprocessed_sequence: np.ndarray, device: str) -> np.ndarray:
    x = torch.tensor(preprocessed_sequence, dtype=torch.float32, device=device).unsqueeze(0)  # [1, target_len, feat_dim]
    embedding, _ = bundle.model(x)

    if bundle.normalize_embeddings:
        embedding = torch.nn.functional.normalize(embedding, p=2, dim=1)

    return embedding.cpu().numpy()


def recognize_gesture(embedding: np.ndarray, faiss_index, train_labels, id_to_label, k: int) -> RecognitionResult:
    class_count = len(id_to_label)
    search_k = min(getattr(faiss_index, "ntotal", max(20, k)), max(20, k, class_count * 3))
    scores, candidate_indices = faiss_search(faiss_index, embedding.reshape(-1), search_k)

    best_index = candidate_indices[0]
    if best_index == -1:
        raise ValueError("FAISS returned no valid neighbors")

    predicted_label_id = train_labels[best_index]
    label = str(id_to_label[predicted_label_id])
    score = float(scores[0])

    margin = float("inf")
    for candidate_score, candidate_index in zip(scores[1:], candidate_indices[1:]):
        if candidate_index == -1:
            continue

        candidate_label_id = train_labels[candidate_index]
        candidate_label = str(id_to_label[candidate_label_id])
        if candidate_label != label:
            margin = score - float(candidate_score)
            break

    return RecognitionResult(label=label, score=score, margin=margin)


def try_recognize(raw_sequence, encoder_bundle, faiss_index, train_labels, id_to_label, device, target_len, k=1):
    try:
        processed = preprocess(raw_sequence, target_len=target_len)
        embedding = embed_sequence(encoder_bundle, processed, device=device)
        return recognize_gesture(embedding, faiss_index, train_labels, id_to_label, k=k)
    except Exception as exc:
        print(f"Error processing: {exc}")
        return None


@dataclass
class BaseGestureRecognizer:
    encoder_bundle: EncoderBundle
    faiss_index: object
    train_labels: np.ndarray
    id_to_label: np.ndarray
    device: str
    activity_start_frames: int = 3
    activity_end_frames: int = 10
    target_len: int = 60
    top_k: int = 1

    state: RecognizerState = field(default=RecognizerState.WAITING, init=False)
    active_streak: int = field(default=0, init=False)
    inactive_streak: int = field(default=0, init=False)

    @property
    def status(self) -> str:
        return self.state.name

    def _update_streaks(self, hand_detected: bool) -> None:
        if hand_detected:
            self.active_streak += 1
            self.inactive_streak = 0
        else:
            self.inactive_streak += 1
            self.active_streak = 0

    def _recognize(self, sequence: np.ndarray) -> RecognitionResult | None:
        return try_recognize(
            sequence,
            self.encoder_bundle,
            self.faiss_index,
            self.train_labels,
            self.id_to_label,
            self.device,
            self.target_len,
            self.top_k,
        )


@dataclass
class GestureSegmenter(BaseGestureRecognizer):
    max_buffer_frames: int = 150
    min_gesture_frames: int = 8

    buffer: deque = field(init=False)

    def __post_init__(self):
        self.buffer = deque(maxlen=self.max_buffer_frames)

    def update(self, feature_vector: np.ndarray, hand_detected: bool) -> RecognitionResult | None:
        self._update_streaks(hand_detected)

        if self.state == RecognizerState.WAITING:
            if self.active_streak >= self.activity_start_frames:
                self.state = RecognizerState.RECORDING
                self.buffer.clear()
                self.buffer.append(feature_vector)
            return None

        self.buffer.append(feature_vector)

        if self.inactive_streak >= self.activity_end_frames or len(self.buffer) >= self.max_buffer_frames:
            self.state = RecognizerState.WAITING
            sequence = np.array(self.buffer, dtype=np.float32)
            self.buffer.clear()
            self.active_streak = 0
            self.inactive_streak = 0
            if sequence.shape[0] < self.min_gesture_frames:
                return None

            return self._recognize(sequence)

        return None


@dataclass
class SlidingWindowRecognizer(BaseGestureRecognizer):
    activity_end_frames: int = 3
    window_frames: int = 90
    step_frames: int = 5
    min_score: float = 0.75
    min_margin: float = 0.03
    custom_min_score: float = 0.5
    custom_min_margin: float = 0.03
    stability_window: int = 4
    required_votes: int = 3
    cooldown_frames: int = 20
    min_hand_ratio: float = 0.5
    switch_required_votes: int = 3
    is_custom_database: bool = False

    frame_buffer: deque = field(init=False)
    hand_buffer: deque = field(init=False)
    candidates: deque[RecognitionResult] = field(init=False)
    switch_candidates: deque[RecognitionResult] = field(init=False)
    frame_count: int = field(default=0, init=False)
    cooldown_left: int = field(default=0, init=False)
    locked_label: str | None = field(default=None, init=False)
    last_candidate: RecognitionResult | None = field(default=None, init=False)

    def __post_init__(self):
        self.frame_buffer = deque(maxlen=self.window_frames)
        self.hand_buffer = deque(maxlen=self.window_frames)
        self.candidates = deque(maxlen=self.stability_window)
        self.switch_candidates = deque(maxlen=self.stability_window)

    def update(self, feature_vector: np.ndarray, hand_detected: bool) -> RecognitionResult | None:
        self._update_streaks(hand_detected)

        if self.state == RecognizerState.WAITING:
            if self.active_streak >= self.activity_start_frames:
                self.state = RecognizerState.RECORDING
                self._clear_recording_buffers()
                self._append_frame(feature_vector, hand_detected)
            return None

        self.frame_count += 1
        self._append_frame(feature_vector, hand_detected)

        if self.cooldown_left > 0:
            self.cooldown_left -= 1

        if self.inactive_streak >= self.activity_end_frames:
            self._reset()
            return None

        if not hand_detected:
            return None

        if len(self.frame_buffer) < self.window_frames:
            return None

        if self.frame_count % self.step_frames != 0:
            return None

        if np.mean(self.hand_buffer) < self.min_hand_ratio:
            self._reset()
            return None

        result = self._recognize(np.array(self.frame_buffer, dtype=np.float32))

        if result is None or not self._is_confident(result):
            self.candidates.clear()
            self.last_candidate = result
            return None

        self.last_candidate = result

        if self.locked_label is not None:
            return self._handle_locked_state(result)

        self.candidates.append(result)
        stable_result = self._stable_result(self.candidates, self.required_votes)
        if stable_result is None:
            return None

        self.locked_label = stable_result.label
        self.cooldown_left = self.cooldown_frames
        self.candidates.clear()
        return stable_result

    def _is_confident(self, result: RecognitionResult) -> bool:
        if self.is_custom_database:
            return result.score >= self.custom_min_score and result.margin >= self.custom_min_margin
        return result.score >= self.min_score and result.margin >= self.min_margin

    def _stable_result(self, results: deque[RecognitionResult], required_votes: int) -> RecognitionResult | None:
        if len(results) < results.maxlen:
            return None

        labels = [result.label for result in results]
        best_label = max(set(labels), key=labels.count)
        if labels.count(best_label) < required_votes or self.cooldown_left > 0:
            return None

        latest = results[-1]
        if latest.label != best_label:
            return None

        return latest

    def _handle_locked_state(self, result: RecognitionResult) -> RecognitionResult | None:
        if result.label == self.locked_label:
            self.switch_candidates.clear()
            return None

        self.switch_candidates.append(result)
        stable_result = self._stable_result(self.switch_candidates, self.switch_required_votes)
        if stable_result is None:
            return None

        self.locked_label = stable_result.label
        self.cooldown_left = self.cooldown_frames
        self.switch_candidates.clear()
        return stable_result

    def _reset(self) -> None:
        self.state = RecognizerState.WAITING
        self.active_streak = 0
        self.inactive_streak = 0
        self._clear_recording_buffers()

    def _append_frame(self, feature_vector: np.ndarray, hand_detected: bool) -> None:
        self.frame_buffer.append(feature_vector)
        self.hand_buffer.append(hand_detected)

    def _clear_recording_buffers(self) -> None:
        self.frame_buffer.clear()
        self.hand_buffer.clear()
        self.candidates.clear()
        self.switch_candidates.clear()
        self.frame_count = 0
        self.cooldown_left = 0
        self.locked_label = None
        self.last_candidate = None


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
