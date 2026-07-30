from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch
from Recognition.faiss_dtw import build_faiss_index
from Models.Transformer_encoder import TransformerEncoder
from DataProcessing.collector import create_landmarkers, process_video
from DataProcessing.preprocessing import preprocess
from Recognition.recognition_utils import load_encoder, embed_sequence

MODEL = TransformerEncoder

TRAIN_EMBEDDINGS_PATH = Path(f"Models/{MODEL.__name__}_Checkpoints/train_embeddings.npz")
MODEL_CHECKPOINT_PATH = Path(f"Models/{MODEL.__name__}_Checkpoints/best_encoder.pt")
FAISS_DB_DIR = Path(f"Recognition/{MODEL.__name__}_db")
FAISS_INDEX_PATH = FAISS_DB_DIR / "index.faiss"
FAISS_LABELS_PATH = FAISS_DB_DIR / "index_labels.npz"

TARGET_LEN = 60

def build_index_from_arrays(
    embeddings: np.ndarray,
    labels: np.ndarray,
    id_to_label: np.ndarray,
    output_dir: Path = FAISS_DB_DIR,
) -> None:
    output_dir = Path(output_dir)
    faiss_index_path = output_dir / "index.faiss"
    faiss_labels_path = output_dir / "index_labels.npz"
    output_dir.mkdir(parents=True, exist_ok=True)

    build_faiss_index(embeddings, faiss_index_path)
    np.savez(faiss_labels_path, labels=labels, id_to_label=id_to_label)

    print(f"FAISS index built from {embeddings.shape[0]} embeddings -> {faiss_index_path}")
    print(f"Labels saved -> {faiss_labels_path}")


def build_index_from_npz(
    npz_path: Path = TRAIN_EMBEDDINGS_PATH,
    output_dir: Path = FAISS_DB_DIR,
) -> None:
    with np.load(npz_path, allow_pickle=True) as data:
        embeddings = data["embeddings"]
        labels = data["labels"]
        id_to_label = data["id_to_label"]
    
    build_index_from_arrays(
        embeddings=embeddings,
        labels=labels,
        id_to_label=id_to_label,
        output_dir=output_dir,
    )


def build_index_from_videos(
    dataset_dir: Path,
    checkpoint_path: Path = MODEL_CHECKPOINT_PATH,
    device: str | None = None,
    target_len: int = TARGET_LEN,
    output_dir: Path = FAISS_DB_DIR,
) -> None:
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    dataset_dir = Path(dataset_dir)
    gesture_dirs = sorted(d for d in dataset_dir.iterdir() if d.is_dir())

    if not gesture_dirs:
        raise ValueError(f"[build_faiss_db] Dir not found: {dataset_dir}")

    class_names = [d.name for d in gesture_dirs]
    label_to_id = {name: idx for idx, name in enumerate(class_names)}
    id_to_label = np.array(class_names)

    print(f"[build_faiss_db] Found {len(class_names)} classes")
    print(f"[build_faiss_db] Loading encoder from: {checkpoint_path} (device={device})")

    encoder_bundle = load_encoder(checkpoint_path, MODEL, device)

    all_embeddings: list[np.ndarray] = []
    all_labels: list[int] = []

    hands, pose = create_landmarkers()
    timestamp_offset_ms = 0

    try:
        for gesture_dir in gesture_dirs:
            gesture_name = gesture_dir.name
            label_id = label_to_id[gesture_name]
            video_files = sorted(gesture_dir.glob("*.mp4"))

            if not video_files:
                print(f"  [SKIP] {gesture_name}: .mp4 not found ")
                continue

            print(f"\n  Video processing '{gesture_name}' ({len(video_files)})...")

            for video_path in video_files:
                sequence, timestamp_offset_ms = process_video(
                    video_path, hands, pose, timestamp_offset_ms
                )

                if sequence is None or sequence.shape[0] < 8:
                    print(f"    [SKIP] {video_path.name}: too short sequence")
                    continue

                try:
                    processed = preprocess(sequence, target_len=target_len)
                    embedding = embed_sequence(encoder_bundle, processed, device=device)

                    all_embeddings.append(embedding.reshape(-1))
                    all_labels.append(label_id)

                    print(f"    {video_path.name}: OK  embedding shape={embedding.shape}")
                except Exception as exc:
                    print(f"    [ERR] {video_path.name}: {exc}")

    finally:
        hands.close()
        pose.close()

    if not all_embeddings:
        raise RuntimeError("[build_faiss_db] No embeddings were generated.")

    embeddings_array = np.stack(all_embeddings, axis=0).astype(np.float32)
    labels_array = np.array(all_labels, dtype=np.int64)

    print(f"\n[build_faiss_db] Generated {embeddings_array.shape[0]} embeddings from {len(class_names)} classes.")

    build_index_from_arrays(
        embeddings=embeddings_array,
        labels=labels_array,
        id_to_label=id_to_label,
        output_dir=output_dir,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Build FAISS database from .npz file or from raw mp4 recordings."
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    # --- npz mode ---
    p_npz = subparsers.add_parser("npz", help="Build index from train_embeddings.npz file")
    p_npz.add_argument("--path", type=Path, default=TRAIN_EMBEDDINGS_PATH,
                       help="Path to .npz file with embeddings")
    p_npz.add_argument("--key", type=str, default="embeddings",
                       help="Key of embeddings in .npz file")
    p_npz.add_argument("--output-dir", type=Path, default=FAISS_DB_DIR,
                       help="Directory where index.faiss and index_labels.npz are written")

    # --- video mode ---
    p_vid = subparsers.add_parser("videos", help="Build index directly from mp4 recordings")
    p_vid.add_argument("dataset_dir", type=Path,
                       help="Directory with gesture class subfolders (e.g. Dataset_test/)")
    p_vid.add_argument("--checkpoint", type=Path, default=MODEL_CHECKPOINT_PATH,
                       help="Path to encoder checkpoint (.pt)")
    p_vid.add_argument("--device", type=str, default=None,
                       help="'cuda' or 'cpu' (autodetect)")
    p_vid.add_argument("--target-len", type=int, default=TARGET_LEN,
                       help=f"Target sequence length (default: {TARGET_LEN})")
    p_vid.add_argument("--output-dir", type=Path, default=FAISS_DB_DIR,
                       help="Directory where index.faiss and index_labels.npz are written")

    args = parser.parse_args()

    if args.mode == "npz":
        build_index_from_npz(npz_path=args.path, output_dir=args.output_dir)
    elif args.mode == "videos":
        build_index_from_videos(
            dataset_dir=args.dataset_dir,
            checkpoint_path=args.checkpoint,
            device=args.device,
            target_len=args.target_len,
            output_dir=args.output_dir,
        )
