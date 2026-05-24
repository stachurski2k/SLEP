import os
import numpy as np
import torch
import random
from torch.utils.data import Dataset
from sklearn.model_selection import train_test_split
from DataProcessing.preprocessing import preprocess


class GestureDataset(Dataset):
    def __init__(self, paths_with_labels: list, label_map: dict):
        self.samples   = paths_with_labels
        self.label_map = label_map
        self.labels    = [label_map[l] for _, l in paths_with_labels]
 
    def __len__(self):
        return len(self.samples)
 
    def __getitem__(self, idx):
        path, label_str = self.samples[idx]
        seq = np.load(path)
        seq = preprocess(seq)
        return (
            torch.tensor(seq, dtype=torch.float32),
            self.label_map[label_str],
        )

    
def build_splits(landmarks_dir: str, val_ratio=0.2, seed=42):
    label_map   = {}
    train_paths = []
    val_paths   = []
 
    labels = sorted(os.listdir(landmarks_dir))
 
    for idx, label_str in enumerate(labels):
        label_map[label_str] = idx
        label_dir = os.path.join(landmarks_dir, label_str)
 
        paths = [
            (os.path.join(label_dir, f), label_str)
            for f in os.listdir(label_dir)
            if f.endswith(".npy")
        ]
 
        if len(paths) < 2:
            print(f"{label_str}: tylko {len(paths)} nagranie — "
                  f"całość trafia do train")
            train_paths.extend(paths)
            continue
 
        t, v = train_test_split(paths, test_size=val_ratio,
                                random_state=seed)
        train_paths.extend(t)
        val_paths.extend(v)
 
    print(f"Train: {len(train_paths)} próbek | "
          f"Val: {len(val_paths)} próbek | "
          f"Klas: {len(label_map)}")
 
    return train_paths, val_paths, label_map