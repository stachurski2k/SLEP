import os
import numpy as np
import torch
import random
from torch.utils.data import Dataset
from sklearn.model_selection import train_test_split
from DataProcessing.preprocessing import preprocess


class GestureDataset(Dataset):
    def __init__(self, paths: list, label_map: dict, augmentor=None):
        self.label_map = label_map
        self.augmentor = augmentor
        self.labels = []
        self.data = []        
        for path, label_str in paths:
            seq = np.load(path)
            seq = preprocess(seq)
            self.data.append(seq.astype(np.float32)) 
            self.labels.append(label_map[label_str])

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        seq = self.data[idx]                          
        if self.augmentor is not None:
            seq = self.augmentor(seq)             
        return torch.tensor(seq, dtype=torch.float32), self.labels[idx]
        
    
def build_splits(landmarks_dir: str, val_ratio=0.2, seed=42):
    label_map   = {}
    train_paths = []
    val_paths   = []
 
    labels = sorted(os.listdir(landmarks_dir))
 
    for idx, label_str in enumerate(labels):
        # add folder name to label map
        label_map[label_str] = idx
        label_dir = os.path.join(landmarks_dir, label_str)

        # add files to paths with folder name as label
        paths = []
        for f in sorted(os.listdir(label_dir)):
            if f.endswith(".npy"):
                full_path = os.path.join(label_dir,f)
                paths.append((full_path, label_str))
        if len(paths) < 2:
            print(f"{label_str}: only {len(paths)} videos - all goes to train")
            train_paths.extend(paths)
            continue
        
        # split into train and val
        t, v = train_test_split(paths, test_size=val_ratio,
                                random_state=seed)
        train_paths.extend(t)
        val_paths.extend(v)
 
    print(f"Train: {len(train_paths)} videos | "
          f"Val: {len(val_paths)} videos | "
          f"Classes: {len(label_map)}")
 
    return train_paths, val_paths, label_map
