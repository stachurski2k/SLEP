"""Model loading, FAISS lookup, and the end-to-end video -> prediction pipeline."""
import queue
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

import faiss
import numpy as np
import torch
import torch.nn as nn

from app.config import Settings
from app.landmarks import create_landmarkers, preprocess, process_video
from app.model import TransformerEncoder


class NoGestureDetectedError(Exception):
    """Raised when a video yields no usable landmark sequence."""


class PoolExhaustedError(Exception):
    """Raised when no landmarker is free within the checkout timeout."""


# --- MediaPipe landmarker pool ----------------------------------------------
#
# HandLandmarker/PoseLandmarker in RunningMode.VIDEO require strictly
# increasing timestamps per instance and are not safe to call concurrently on
# the same instance. Each request checks out one (hands, pose) pair, uses it
# for exactly one video, and returns it - carrying forward its own running
# timestamp offset (same pattern as the parallel workers in
# research/test_version/DataProcessing/collector.py).


@dataclass
class PooledLandmarker:
    hands: object
    pose: object
    timestamp_offset_ms: int = 0


class LandmarkerPool:
    def __init__(self, size: int, hand_model_path: Path, pose_model_path: Path):
        self._queue: queue.Queue[PooledLandmarker] = queue.Queue(maxsize=size)
        for _ in range(size):
            hands, pose = create_landmarkers(hand_model_path, pose_model_path)
            self._queue.put(PooledLandmarker(hands=hands, pose=pose))

    @contextmanager
    def borrow(self, timeout: float):
        try:
            item = self._queue.get(timeout=timeout)
        except queue.Empty as exc:
            raise PoolExhaustedError("No landmarker available; server is at capacity") from exc
        try:
            yield item
        finally:
            self._queue.put(item)

    def close(self) -> None:
        while not self._queue.empty():
            item = self._queue.get_nowait()
            item.hands.close()
            item.pose.close()


# --- Encoder ------------------------------------------------------------


@dataclass
class EncoderBundle:
    model: nn.Module
    label_map: dict
    normalize_embeddings: bool


def load_encoder(checkpoint_path: Path, device: str) -> EncoderBundle:
    checkpoint = torch.load(checkpoint_path, map_location=device)
    config = checkpoint["config"]
    model = TransformerEncoder(
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
    x = torch.tensor(preprocessed_sequence, dtype=torch.float32, device=device).unsqueeze(0)
    embedding, _ = bundle.model(x)

    if bundle.normalize_embeddings:
        embedding = torch.nn.functional.normalize(embedding, p=2, dim=1)

    return embedding.cpu().numpy()


# --- FAISS lookup ------------------------------------------------------------


def build_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    emb = np.ascontiguousarray(embeddings, dtype=np.float32)
    faiss.normalize_L2(emb)
    index = faiss.IndexFlatIP(emb.shape[1])
    index.add(emb)
    return index


def faiss_search(index: faiss.Index, query_embedding: np.ndarray, k: int):
    query = np.ascontiguousarray(query_embedding.reshape(1, -1), dtype=np.float32)
    faiss.normalize_L2(query)
    distances, indices = index.search(query, k)
    return distances[0], indices[0]


@dataclass
class RecognitionResult:
    label: str
    score: float
    margin: float


def recognize_gesture(embedding: np.ndarray, faiss_index, train_labels, id_to_label, k: int) -> RecognitionResult:
    class_count = len(id_to_label)
    search_k = min(faiss_index.ntotal, max(20, k, class_count * 3))
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


# --- End-to-end pipeline ------------------------------------------------------


@dataclass
class InferenceService:
    encoder_bundle: EncoderBundle
    faiss_index: faiss.Index
    train_labels: np.ndarray
    id_to_label: np.ndarray
    landmarker_pool: LandmarkerPool
    device: str
    target_len: int
    min_gesture_frames: int
    faiss_search_k: int
    landmarker_checkout_timeout_seconds: float
    _forward_lock: threading.Lock = field(default_factory=threading.Lock)

    @classmethod
    def from_settings(cls, settings: Settings) -> "InferenceService":
        encoder_bundle = load_encoder(settings.encoder_checkpoint_path, settings.device)

        with np.load(settings.train_embeddings_path, allow_pickle=True) as data:
            embeddings = data["embeddings"]
            train_labels = data["labels"]
            id_to_label = data["id_to_label"]
        faiss_index = build_faiss_index(embeddings)

        landmarker_pool = LandmarkerPool(
            size=settings.landmarker_pool_size,
            hand_model_path=settings.hand_model_path,
            pose_model_path=settings.pose_model_path,
        )

        return cls(
            encoder_bundle=encoder_bundle,
            faiss_index=faiss_index,
            train_labels=train_labels,
            id_to_label=id_to_label,
            landmarker_pool=landmarker_pool,
            device=settings.device,
            target_len=settings.target_len,
            min_gesture_frames=settings.min_gesture_frames,
            faiss_search_k=settings.faiss_search_k,
            landmarker_checkout_timeout_seconds=settings.landmarker_checkout_timeout_seconds,
        )

    def predict(self, video_path: Path) -> RecognitionResult:
        with self.landmarker_pool.borrow(timeout=self.landmarker_checkout_timeout_seconds) as item:
            sequence, item.timestamp_offset_ms = process_video(
                video_path, item.hands, item.pose, item.timestamp_offset_ms
            )

        if sequence is None or sequence.shape[0] < self.min_gesture_frames:
            raise NoGestureDetectedError(
                f"Video produced no usable landmark sequence (need >= {self.min_gesture_frames} frames)"
            )

        processed = preprocess(sequence, target_len=self.target_len)

        with self._forward_lock:
            embedding = embed_sequence(self.encoder_bundle, processed, device=self.device)

        return recognize_gesture(
            embedding, self.faiss_index, self.train_labels, self.id_to_label, k=self.faiss_search_k
        )

    def close(self) -> None:
        self.landmarker_pool.close()
