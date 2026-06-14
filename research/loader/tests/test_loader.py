import sys
import os
import torch
import numpy as np
from pathlib import Path

# Add package root to sys.path so we can import modules
sys.path.append(str(Path(__file__).parent.parent))

from landmark_dataset import get_landmark_dataloader
from features.enhancer import FeatureEnhancer

def test_feature_enhancer():
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data" / "train_landmarks_npy"
    
    print(f"Searching for data in: {data_dir}")
    
    from utils.get_file_paths import get_file_paths
    try:
        file_paths, labels = get_file_paths(data_dir)
        print(f"Found {len(file_paths)} paths and {len(labels)} labels.")
    except Exception as e:
        print(f"Error gathering paths: {e}")
        return

    # Check a raw file to understand its dimensions
    raw_data = np.load(file_paths[0])
    raw_tensor = torch.tensor(raw_data, dtype=torch.float32)
    print(f"Raw shape of sample 0: {raw_tensor.shape}")

    # Initialize FeatureEnhancers with different configurations
    print("\n--- Testing FeatureEnhancer Configurations ---")
    
    # 1. Full Enhancement (keypoint selection + relative hands + distances + velocities)
    enhancer_full = FeatureEnhancer(
        use_relative_hands=True,
        use_distances=True,
        use_velocities=True,
        select_keypoints=True
    )
    enhanced_full = enhancer_full(raw_tensor)
    print(f"1. Enhanced Full (Select Keypoints + Rel Hands + Distances + Velocity) shape: {enhanced_full.shape}")

    # 2. No velocities
    enhancer_no_vel = FeatureEnhancer(
        use_relative_hands=True,
        use_distances=True,
        use_velocities=False,
        select_keypoints=True
    )
    enhanced_no_vel = enhancer_no_vel(raw_tensor)
    print(f"2. No Velocity shape: {enhanced_no_vel.shape}")

    # 3. No keypoint selection (using all raw keypoints)
    enhancer_all_kp = FeatureEnhancer(
        use_relative_hands=True,
        use_distances=True,
        use_velocities=False,
        select_keypoints=False
    )
    enhanced_all_kp = enhancer_all_kp(raw_tensor)
    print(f"3. All Keypoints (No Select) shape: {enhanced_all_kp.shape}")

    # Test DataLoader with FeatureEnhancer
    print("\n--- Testing DataLoader with FeatureEnhancer ---")
    try:
        dataloader = get_landmark_dataloader(
            file_paths=file_paths,
            labels=labels,
            batch_size=8,
            shuffle=True,
            num_frames=100,
            transform=enhancer_full
        )
        print("DataLoader with FeatureEnhancer initialized.")
        
        # Pull first batch
        for batch_idx, (landmarks, batch_labels) in enumerate(dataloader):
            print(f"Batch {batch_idx + 1}:")
            print(f" - Landmarks shape: {landmarks.shape} (Expected: [batch_size, num_frames, features_dim])")
            print(f" - Labels shape: {batch_labels.shape}")
            break
            
    except Exception as e:
        print(f"Error in DataLoader test: {e}")

if __name__ == "__main__":
    test_feature_enhancer()
