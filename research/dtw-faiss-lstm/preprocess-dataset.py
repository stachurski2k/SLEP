import cv2
import mediapipe as mp
import numpy as np
import os
import argparse
import csv
from pathlib import Path
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from tqdm import tqdm

def get_args():
    parser = argparse.ArgumentParser(description="Preprocess dataset using MediaPipe Holistic")
    parser.add_argument("dataset_path", type=str, help="Path to the extracted dataset")
    parser.add_argument("--overlay", action="store_true", help="Create a dataset with landmarks overlayed on videos")
    return parser.parse_args()

def create_holistic_landmarker():
    base_options = python.BaseOptions(model_asset_path='weights/holistic_landmarker.task')
    options = vision.HolisticLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        output_face_blendshapes=False,
        output_segmentation_mask=False
    )
    return vision.HolisticLandmarker.create_from_options(options)

def draw_landmarks(image, detection_result):
    if not detection_result:
        return image

    annotated_image = np.copy(image)
    height, width, _ = image.shape

    def draw_list(landmarks, color):
        for lm in landmarks:
            cx, cy = int(lm.x * width), int(lm.y * height)
            cv2.circle(annotated_image, (cx, cy), 2, color, -1)

    # Draw face (blue)
    if detection_result.face_landmarks:
        draw_list(detection_result.face_landmarks, (255, 0, 0))

    # Draw pose (green)
    if detection_result.pose_landmarks:
        draw_list(detection_result.pose_landmarks, (0, 255, 0))

    # Draw left hand (red)
    if detection_result.left_hand_landmarks:
        draw_list(detection_result.left_hand_landmarks, (0, 0, 255))

    # Draw right hand (yellow)
    if detection_result.right_hand_landmarks:
        draw_list(detection_result.right_hand_landmarks, (0, 255, 255))

    return annotated_image

def get_landmark_header():
    header = []
    # Pose: 33 landmarks (x, y, z, visibility)
    for i in range(33):
        header.extend([f"pose_x_{i}", f"pose_y_{i}", f"pose_z_{i}", f"pose_v_{i}"])
    # Face: 468 landmarks (x, y, z)
    for i in range(468):
        header.extend([f"face_x_{i}", f"face_y_{i}", f"face_z_{i}"])
    # Left Hand: 21 landmarks (x, y, z)
    for i in range(21):
        header.extend([f"lh_x_{i}", f"lh_y_{i}", f"lh_z_{i}"])
    # Right Hand: 21 landmarks (x, y, z)
    for i in range(21):
        header.extend([f"rh_x_{i}", f"rh_y_{i}", f"rh_z_{i}"])
    return header

def extract_landmarks(detection_result):
    row = []
    
    # Pose
    if detection_result and detection_result.pose_landmarks:
        for lm in detection_result.pose_landmarks:
            row.extend([lm.x, lm.y, lm.z, lm.visibility])
    else:
        row.extend([0.0] * (33 * 4))

    # Face
    if detection_result and detection_result.face_landmarks:
        for lm in detection_result.face_landmarks:
            row.extend([lm.x, lm.y, lm.z])
    else:
        row.extend([0.0] * (468 * 3))

    # Left Hand
    if detection_result and detection_result.left_hand_landmarks:
        for lm in detection_result.left_hand_landmarks:
            row.extend([lm.x, lm.y, lm.z])
    else:
        row.extend([0.0] * (21 * 3))

    # Right Hand
    if detection_result and detection_result.right_hand_landmarks:
        for lm in detection_result.right_hand_landmarks:
            row.extend([lm.x, lm.y, lm.z])
    else:
        row.extend([0.0] * (21 * 3))

    return row

def process_video(video_path, processed_dir, overlay_dir, landmarker):
    video_path = Path(video_path)
    cap = cv2.VideoCapture(str(video_path))
    
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # CSV output
    csv_path = processed_dir / video_path.parent.name / f"{video_path.stem}.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Video output for overlay
    video_writer = None
    if overlay_dir:
        overlay_video_path = overlay_dir / video_path.parent.name / f"{video_path.name}"
        overlay_video_path.parent.mkdir(parents=True, exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(str(overlay_video_path), fourcc, fps, (width, height))

    with open(csv_path, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(get_landmark_header())
        
        frame_idx = 0
        last_timestamp_ms = -1
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert to RGB for MediaPipe
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            
            # Run inference
            timestamp_ms = int(frame_idx * 1000 / fps)
            if timestamp_ms <= last_timestamp_ms:
                timestamp_ms = last_timestamp_ms + 1
            last_timestamp_ms = timestamp_ms
            
            result = landmarker.detect_for_video(mp_image, timestamp_ms)
            
            # Save landmarks
            writer.writerow(extract_landmarks(result))
            
            # Save overlay video
            if video_writer:
                annotated_frame = draw_landmarks(frame, result)
                video_writer.write(annotated_frame)
            
            frame_idx += 1

    cap.release()
    if video_writer:
        video_writer.release()

def main():
    args = get_args()
    dataset_path = Path(args.dataset_path)
    
    if not dataset_path.exists():
        print(f"Error: Dataset path {dataset_path} does not exist.")
        return

    dataset_name = dataset_path.name
    processed_dir = dataset_path.parent / f"{dataset_name}-processed"
    overlay_dir = None
    if args.overlay:
        overlay_dir = dataset_path.parent / f"{dataset_name}-overlay"
        overlay_dir.mkdir(parents=True, exist_ok=True)
    
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Get all video files
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv')
    all_videos = []
    for class_dir in dataset_path.iterdir():
        if class_dir.is_dir():
            for video_file in class_dir.iterdir():
                if video_file.suffix.lower() in video_extensions:
                    all_videos.append(video_file)

    print(f"Found {len(all_videos)} videos in {len(list(dataset_path.iterdir()))} classes.")
    
    for video_file in tqdm(all_videos, desc="Processing videos"):
        landmarker = create_holistic_landmarker()
        process_video(video_file, processed_dir, overlay_dir, landmarker)
        landmarker.close()

    print("Processing complete.")

if __name__ == "__main__":
    main()
