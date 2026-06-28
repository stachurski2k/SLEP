import os
from pathlib import Path
from typing import List, Tuple, Union

def get_file_paths(data_dir: Union[str, Path], zero_indexed: bool = True) -> Tuple[List[Path], List[int]]:
    """
    Args:
        data_dir: Path to the directory containing .npy files (e.g., 'data/train_landmarks_npy').
        zero_indexed: If True, labels are converted to 0-indexed 
                      (required by PyTorch CrossEntropyLoss, among others).
    Returns:
        A tuple (file_paths, labels) ready to be passed to LandmarkDataset / get_landmark_dataloader.
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Directory {data_path} does not exist.")

    file_paths = sorted(list(data_path.glob("*.npy")))
    if not file_paths:
        raise ValueError(f"Not found .npy file in {data_path}.")

    labels = []
    for path in file_paths:
        try:
            label_str = path.stem.split('_')[0]
            labels.append(int(label_str))
        except (IndexError, ValueError):
            raise ValueError(f"Can't parse label from : {path.name}")

    # Dostosowanie do indeksowania od 0 (ciągłe indeksy 0..N-1 dla PyTorcha)
    if zero_indexed and labels:
        unique_labels = sorted(list(set(labels)))
        label_to_idx = {lbl: idx for idx, lbl in enumerate(unique_labels)}
        labels = [label_to_idx[lbl] for lbl in labels]

    return file_paths, labels
