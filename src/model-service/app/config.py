from functools import lru_cache
from pathlib import Path

import torch
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STORAGE_DIR = PROJECT_ROOT / "storage"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MODEL_SERVICE_", env_file=".env", extra="ignore")

    hand_model_path: Path = STORAGE_DIR / "mediapipe" / "hand_landmarker.task"
    pose_model_path: Path = STORAGE_DIR / "mediapipe" / "pose_landmarker_full.task"
    encoder_checkpoint_path: Path = STORAGE_DIR / "encoder" / "best_encoder.pt"
    train_embeddings_path: Path = STORAGE_DIR / "embeddings" / "train_embeddings.npz"

    device: str = Field(default_factory=lambda: "cuda" if torch.cuda.is_available() else "cpu")

    landmarker_pool_size: int = 2
    landmarker_checkout_timeout_seconds: float = 30.0

    target_len: int = 60
    min_gesture_frames: int = 8
    faiss_search_k: int = 10

    max_upload_mb: int = 200


@lru_cache
def get_settings() -> Settings:
    return Settings()
