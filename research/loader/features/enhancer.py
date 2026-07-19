import torch

class FeatureEnhancer:
    """
    Enhances raw MediaPipe Holistic landmarks by extracting relative coordinates,
    distances, velocities, and optionally performing keypoint selection.
    """
    def __init__(self, 
                 use_relative_hands: bool = True,
                 use_distances: bool = True,
                 use_velocities: bool = True,
                 select_keypoints: bool = True):
        self.use_relative_hands = use_relative_hands
        self.use_distances = use_distances
        self.use_velocities = use_velocities
        self.select_keypoints = select_keypoints

    def __call__(self, landmarks_tensor: torch.Tensor) -> torch.Tensor:
        seq_len, num_features = landmarks_tensor.shape
        
        # Fallback if dimensions don't match standard MediaPipe Holistic layout (at least 1629 coords)
        if num_features < 1629:
            if self.use_velocities:
                velocity = torch.zeros_like(landmarks_tensor)
                velocity[1:] = landmarks_tensor[1:] - landmarks_tensor[:-1]
                return torch.cat([landmarks_tensor, velocity], dim=-1)
            return landmarks_tensor

        # MediaPipe Holistic keypoint dimensions:
        # Pose: 33 keypoints * 3 (x, y, z) = 99 features
        # Face: 468 keypoints * 3 (x, y, z) = 1404 features (indices 99 to 1503)
        # Left Hand: 21 keypoints * 3 (x, y, z) = 63 features (indices 1503 to 1566)
        # Right Hand: 21 keypoints * 3 (x, y, z) = 63 features (indices 1566 to 1629)
        pose = landmarks_tensor[:, 0:99].reshape(seq_len, 33, 3)
        face = landmarks_tensor[:, 99:1503].reshape(seq_len, 468, 3)
        left_hand = landmarks_tensor[:, 1503:1566].reshape(seq_len, 21, 3)
        right_hand = landmarks_tensor[:, 1566:1629].reshape(seq_len, 21, 3)

        features_list = []

        # 1. Keypoint Selection (reducing dimensionality and noise)
        if self.select_keypoints:
            pose_indices = [11, 12, 13, 14, 15, 16, 23, 24]
            selected_pose = pose[:, pose_indices, :]
            
            face_indices = [0, 33, 133, 263, 362, 13, 14]
            selected_face = face[:, face_indices, :]
            
            features_list.append(selected_pose.reshape(seq_len, -1))
            features_list.append(selected_face.reshape(seq_len, -1))
        else:
            features_list.append(pose.reshape(seq_len, -1))
            features_list.append(face.reshape(seq_len, -1))

        # 2. Hand Relative Coordinates (translation-invariance)
        if self.use_relative_hands:
            left_wrist = left_hand[:, 0:1, :]
            left_hand_rel = left_hand - left_wrist
            
            right_wrist = right_hand[:, 0:1, :]
            right_hand_rel = right_hand - right_wrist
            
            features_list.append(left_hand_rel.reshape(seq_len, -1))
            features_list.append(right_hand_rel.reshape(seq_len, -1))
        else:
            features_list.append(left_hand.reshape(seq_len, -1))
            features_list.append(right_hand.reshape(seq_len, -1))

        # 3. Spatial Dependencies (distances between key joints)
        if self.use_distances:
            lw_rw_dist = torch.norm(left_hand[:, 0, :] - right_hand[:, 0, :], dim=-1, keepdim=True)
            
            nose = face[:, 0, :]
            lw_nose_dist = torch.norm(left_hand[:, 0, :] - nose, dim=-1, keepdim=True)
            rw_nose_dist = torch.norm(right_hand[:, 0, :] - nose, dim=-1, keepdim=True)
            
            l_shoulder = pose[:, 11, :]
            lw_ls_dist = torch.norm(left_hand[:, 0, :] - l_shoulder, dim=-1, keepdim=True)
            r_shoulder = pose[:, 12, :]
            rw_rs_dist = torch.norm(right_hand[:, 0, :] - r_shoulder, dim=-1, keepdim=True)
            
            distances = torch.cat([lw_rw_dist, lw_nose_dist, rw_nose_dist, lw_ls_dist, rw_rs_dist], dim=-1)
            features_list.append(distances)

        # Concatenate spatial features
        spatial_features = torch.cat(features_list, dim=-1)

        # 4. Temporal Dynamics (Velocities)
        if self.use_velocities:
            velocity = torch.zeros_like(spatial_features)
            velocity[1:] = spatial_features[1:] - spatial_features[:-1]
            final_features = torch.cat([spatial_features, velocity], dim=-1)
        else:
            final_features = spatial_features

        return final_features
