"""Fetch model artifacts needed to run the service.

Downloads:
- best_encoder.pt        (Google Drive)         -> storage/encoder/
- train_embeddings.npz   (Google Drive)         -> storage/embeddings/
- hand_landmarker.task   (Google's model CDN)   -> storage/mediapipe/
- pose_landmarker_full.task (Google's model CDN) -> storage/mediapipe/

Usage:
    uv run scripts/fetch_artifacts.py [--force]
"""
import argparse
from pathlib import Path
from urllib.request import urlretrieve

import gdown

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STORAGE_DIR = PROJECT_ROOT / "storage"

# Google Drive file IDs (from shareable links)
ENCODER_CHECKPOINT_DRIVE_ID = "1o_1z-VICTZBdU_lUBpBlcKrnwUPbRIB8"
TRAIN_EMBEDDINGS_DRIVE_ID = "1BZPpKk0O0dHxZU6Sj7CkI1nyFqdip6sJ"

# MediaPipe's public model CDN (same models used during landmark extraction/training)
HAND_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
POSE_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task"


def fetch_from_drive(file_id: str, destination: Path, force: bool) -> None:
    if destination.exists() and not force:
        print(f"  [skip] {destination} already exists")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    gdown.download(id=file_id, output=str(destination), quiet=False)


def fetch_from_url(url: str, destination: Path, force: bool) -> None:
    if destination.exists() and not force:
        print(f"  [skip] {destination} already exists")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    print(f"  Downloading {url} -> {destination}")
    urlretrieve(url, destination)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Re-download even if the file already exists")
    args = parser.parse_args()

    print("Encoder checkpoint:")
    fetch_from_drive(ENCODER_CHECKPOINT_DRIVE_ID, STORAGE_DIR / "encoder" / "best_encoder.pt", args.force)

    print("Train embeddings:")
    fetch_from_drive(TRAIN_EMBEDDINGS_DRIVE_ID, STORAGE_DIR / "embeddings" / "train_embeddings.npz", args.force)

    print("MediaPipe hand landmarker model:")
    fetch_from_url(HAND_MODEL_URL, STORAGE_DIR / "mediapipe" / "hand_landmarker.task", args.force)

    print("MediaPipe pose landmarker model:")
    fetch_from_url(POSE_MODEL_URL, STORAGE_DIR / "mediapipe" / "pose_landmarker_full.task", args.force)

    print("\nAll artifacts fetched.")


if __name__ == "__main__":
    main()
