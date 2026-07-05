from pathlib import Path
import numpy as np
from Recognition.faiss_dtw import build_faiss_index
from Models.Transformer_encoder import TransformerEncoder

MODEL = TransformerEncoder

TRAIN_EMBEDDINGS_PATH = Path(f"Models/{MODEL.__name__}_Checkpoints/train_embeddings.npz")
FAISS_DB_DIR = Path(f"Recognition/{MODEL.__name__}_db")
FAISS_INDEX_PATH = FAISS_DB_DIR / "index.faiss"
FAISS_LABELS_PATH = FAISS_DB_DIR / "index_labels.npz"

_EMBEDDING_KEY_CANDIDATES = ["embeddings", "last_embeddings"]

def _resolve_embedding_key(data: np.lib.npyio.NpzFile, preferred_key: str) -> str:
    candidates = [preferred_key] + [k for k in _EMBEDDING_KEY_CANDIDATES if k != preferred_key]
    for key in candidates:
        if key in data:
            if key != preferred_key:
                print(f"[build_faiss_db] Key '{preferred_key}' not found, using '{key}'.")
            return key
    available = list(data.keys())
    raise KeyError(
        f"[build_faiss_db] Key '{preferred_key}' not found in {data.zip.filename}.\n"
        f"Searched: {candidates}\n"
        f"Available: {available}"
    )



def build_index_from_arrays(embeddings: np.ndarray, labels: np.ndarray, id_to_label: np.ndarray) -> None:
    FAISS_DB_DIR.mkdir(parents=True, exist_ok=True)

    build_faiss_index(embeddings, save_path=str(FAISS_INDEX_PATH))
    np.savez(FAISS_LABELS_PATH, labels=labels, id_to_label=id_to_label)

    print(f"FAISS index built from {embeddings.shape[0]} embeddings -> {FAISS_INDEX_PATH}")
    print(f"Labels saved -> {FAISS_LABELS_PATH}")


def build_index_from_npz(npz_path: Path = TRAIN_EMBEDDINGS_PATH, embedding_key: str = "embeddings") -> None:
    data = np.load(npz_path)
    key = _resolve_embedding_key(data, embedding_key)
    
    build_index_from_arrays(
        embeddings=data[key],
        labels=data["labels"],
        id_to_label=data["id_to_label"],
    )


if __name__ == "__main__":
    build_index_from_npz()