import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np
from pathlib import Path
from typing import List, Union, Callable, Optional, Tuple

class LandmarkDataset(Dataset):
    """
    PyTorch Dataset for MediaPipe Holistic landmark data.
    
    Assumes each input .npy file contains verified landmark coordinates
    with consistent feature dimensions (e.g., 1659 flattened coordinates per frame).
    """
    
    def __init__(self, 
                 file_paths: List[Union[str, Path]], 
                 labels: List[int], 
                 num_frames: Optional[int] = None, 
                 transform: Optional[Callable] = None):
        """
        Args:
            file_paths: List of file paths to .npy files containing extracted landmarks.
            labels: List of integer labels corresponding to each video.
            num_frames: Optional number of frames to determine the training portion.
                        If provided, sequences are sliced or padded to this exact length.
            transform: Optional callable to transform the landmark tensor (e.g., feature engineering).
        """
        assert len(file_paths) == len(labels), "Number of file paths must match number of labels."
        
        self.file_paths = [Path(p) for p in file_paths]
        self.labels = labels
        self.num_frames = num_frames
        self.transform = transform

    def __len__(self) -> int:
        return len(self.file_paths)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        npy_path = self.file_paths[idx]
        
        # Load landmark data from .npy file
        landmarks = np.load(npy_path)
        
        landmarks_tensor = torch.tensor(landmarks, dtype=torch.float32)
        label_tensor = torch.tensor(self.labels[idx], dtype=torch.long)

        # Apply optional transformation / feature engineering
        if self.transform:
            landmarks_tensor = self.transform(landmarks_tensor)

        # Adjust sequence length to the specified number of frames
        if self.num_frames is not None:
            seq_len = landmarks_tensor.shape[0]
            if seq_len > self.num_frames:
                landmarks_tensor = landmarks_tensor[:self.num_frames, :]
            elif seq_len < self.num_frames:
                padding = torch.zeros(self.num_frames - seq_len, landmarks_tensor.shape[1])
                landmarks_tensor = torch.cat((landmarks_tensor, padding), dim=0)

        return landmarks_tensor, label_tensor


def get_landmark_dataloader(file_paths: List[Union[str, Path]], 
                            labels: List[int], 
                            batch_size: int = 32, 
                            shuffle: bool = True, 
                            num_frames: Optional[int] = None, 
                            transform: Optional[Callable] = None, 
                            num_workers: int = 0) -> DataLoader:
    """
    Creates and returns a PyTorch DataLoader for the landmark dataset.
    
    Since input data is verified and maintains consistent structure,
    the default PyTorch collate_fn is used for batching.
    
    Args:
        file_paths: List of paths to .npy landmark files.
        labels: List of integer labels corresponding to the files.
        batch_size: Number of samples per batch.
        shuffle: Whether to shuffle the dataset.
        num_frames: Optional fixed number of frames to slice/pad for training.
        transform: Optional callable for custom tensor transformation.
        num_workers: Number of subprocesses for data loading.
        
    Returns:
        DataLoader object ready for model training or evaluation.
    """
    dataset = LandmarkDataset(
        file_paths=file_paths, 
        labels=labels, 
        num_frames=num_frames, 
        transform=transform
    )
    
    return DataLoader(
        dataset, 
        batch_size=batch_size, 
        shuffle=shuffle, 
        num_workers=num_workers
    )
