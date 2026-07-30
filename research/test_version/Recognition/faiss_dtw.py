from pathlib import Path
import faiss
import numpy as np
from dtaidistance import dtw_ndim

DEFAULT_FAISS_INDEX_PATH = Path("Recognition/faiss_index.faiss")


def build_faiss_index(embeddings, index_path=DEFAULT_FAISS_INDEX_PATH):
    index_path = Path(index_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)

    emb = np.ascontiguousarray(embeddings, dtype=np.float32)
    if emb.ndim != 2:
        raise ValueError(f"Expected embeddings with shape [n_samples, dim], got {emb.shape}")

    faiss.normalize_L2(emb)
    index = faiss.IndexFlatIP(emb.shape[1])
    index.add(emb)
    faiss.write_index(index, str(index_path))
    return index


def load_faiss_index(index_path=DEFAULT_FAISS_INDEX_PATH):
    return faiss.read_index(str(index_path))


def faiss_search(index, query_embedding, k=10):
    query = np.ascontiguousarray(query_embedding.reshape(1, -1), dtype=np.float32)
    faiss.normalize_L2(query)
 
    distances, indices = index.search(query, k)
 
    return indices[0]


def dtw_decider(query_seq, candidate_indices, train_seq, train_labels):
    best_dist = np.inf
    best_label = None

    for idx in candidate_indices:
        dist = dtw_ndim.distance(query_seq, train_seq[idx])

        if dist < best_dist:
            best_dist = dist
            best_label = train_labels[idx]

    return best_label


def benchmark_faiss(index, val_emb, val_labels, train_labels):
    correct = 0
    for emb, true_label in zip(val_emb, val_labels):
        idx = faiss_search(index, emb, k=1)[0]
        pred = train_labels[idx]

        if pred == true_label:
            correct += 1

    return correct / len(val_labels) * 100


def benchmark_faiss_dtw(index, val_emb, val_seq, val_labels, train_seq, train_labels, k=10):
    correct = 0

    for emb, seq, true_label in zip(val_emb, val_seq, val_labels):
        candidates = faiss_search(index, emb, k)
        pred = dtw_decider(seq, candidates, train_seq, train_labels)

        if pred == true_label:
            correct += 1

    return correct / len(val_labels) * 100
