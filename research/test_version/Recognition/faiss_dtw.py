from collections import Counter
import faiss
import numpy as np
from dtaidistance import dtw_ndim
from sklearn.metrics import accuracy_score
import time
from collections import Counter


def build_faiss_index(train_embeddings):
    dim = train_embeddings.shape[1]

    index = faiss.IndexFlatIP(dim)

    faiss.normalize_L2(train_embeddings)

    index.add(train_embeddings.astype(np.float32))

    return index


def faiss_search(index, query_embedding, k=10):

    query = query_embedding.reshape(1, -1).astype(np.float32)

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

def benchmark_faiss(val_emb, val_labels, train_labels, index):
    correct = 0
    for emb, true_label in zip(val_emb, val_labels):

        idx = faiss_search(index, emb, k=1)[0]
        pred = train_labels[idx]

        if pred == true_label:
            correct += 1

    return correct / len(val_labels)*100

def benchmark_faiss_dtw(val_emb,val_seq, val_labels,train_seq,train_labels,index,k=10):
    correct = 0

    for emb, seq, true_label in zip(val_emb, val_seq, val_labels):
        candidates = faiss_search(index,emb,k)
        pred = dtw_decider(seq, candidates, train_seq, train_labels)

        if pred == true_label:
            correct += 1

    return correct / len(val_labels)*100

