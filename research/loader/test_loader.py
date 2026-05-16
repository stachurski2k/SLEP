import os
from pathlib import Path
from data_loader import get_landmark_dataloader, LandmarkDataset
from utils.get_file_paths import get_file_paths
from utils.transform_func import add_5

def test_dataloader():
    
    base_dir = Path(__file__).parent
    data_dir = base_dir / "data" / "train_landmarks_npy"
    
    print(f"Searching for data in: {data_dir}")

    try:
        file_paths, labels = get_file_paths(data_dir)
        print(f"Found {len(file_paths)} paths and  \n{len(labels)} labels.")
        print(f"Unique labels: {set(labels)}")
    except Exception as e:
        print(f"Error gathering paths: {e}")
        return

    batch_size = 32

    print(f"\n######## DataLoadera initialization (batch_size={batch_size})...")

    try:
        dataloader = get_landmark_dataloader(
            file_paths=file_paths,
            labels=labels,
            batch_size=batch_size,
            shuffle=True,
            num_frames=200,
            transform=add_5
        )
        print("DataLoader created.")
    except Exception as e:
        print(f"Error creating DataLoader: {e}")
        return
    

    print(list(dataloader)[0])

    print("\nPobieranie pierwszego batcha danych...")
    try:
        for batch_idx, (landmarks, batch_labels) in enumerate(dataloader):
            print(f"Batch {batch_idx + 1}:")
            print(f" - Landmarks tensor shape: {landmarks.shape}")
            print(f" - Labels tensor shape: {batch_labels.shape}")
            print(f" - Labels list: {batch_labels.tolist()}")
            break 
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_dataloader()
    
