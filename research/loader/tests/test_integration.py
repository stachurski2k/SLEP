import os
import sys
import time
import json
import urllib.request
import numpy as np
import torch
import socket
from pathlib import Path

# Add package root to sys.path
sys.path.append(str(Path(__file__).parent.parent))
from features.enhancer import FeatureEnhancer
from api.client import get_backend_dataloader

# DB and S3 configuration for local host access
def resolve_hosts():
    try:
        socket.gethostbyname("postgres")
        # Inside Docker network
        return "postgres", "http://s3:9000", "http://data-collection-api:5000"
    except socket.gaierror:
        # Outside Docker (local host)
        return "localhost", "http://localhost:9000", "http://localhost:5000"

DB_HOST, S3_URL, BACKEND_URL = resolve_hosts()
DB_PORT = 5432 if DB_HOST == "postgres" else 5435
DB_URL = f"postgresql://postgres:postgres@{DB_HOST}:{DB_PORT}/slep"
S3_BUCKET = "slep-bucket"

def seed_database_and_s3():
    """
    Seeds a mock dataset, video, landmarks, and clip directly in the database,
    and uploads a dummy .npy landmarks file to MinIO.
    """
    print("\n--- Seeding database and MinIO (S3) ---")
    
    # Check if necessary libraries are available locally
    try:
        import boto3
        import psycopg2
    except ImportError as e:
        print(f"Error: Required test libraries not found: {e}")
        print("Please install them: pip install boto3 psycopg2-binary")
        sys.exit(1)

    # 1. Connect to Postgres and insert mock records
    print("Connecting to PostgreSQL...")
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    try:
        # Clean up existing test data
        cur.execute("DELETE FROM clips WHERE video_id = 999")
        cur.execute("DELETE FROM landmarks WHERE video_id = 999")
        cur.execute("DELETE FROM videos WHERE id = 999")
        cur.execute("DELETE FROM datasets WHERE id = 999")
        cur.execute("DELETE FROM gesture_classes WHERE id = 999")
        cur.execute("DELETE FROM gesture_types WHERE id = 999")
        conn.commit()
        
        # Insert test gesture class & type
        cur.execute("INSERT INTO gesture_classes (id, name) VALUES (999, 'TestGesture')")
        cur.execute("INSERT INTO gesture_types (id, name) VALUES (999, 'TestType')")
        
        # Insert test dataset
        cur.execute("INSERT INTO datasets (id, name, description) VALUES (999, 'Integration Test Dataset', 'Mock dataset for integration testing')")
        
        # Insert test video
        cur.execute(
            "INSERT INTO videos (id, name, filepath, description, fps, total_length_seconds, dataset_id) "
            "VALUES (999, 'Test Video', 'videos/test_video.mp4', 'Integration test video', 30, 3.33, 999)"
        )
        
        # Insert test landmark record
        cur.execute(
            "INSERT INTO landmarks (id, filepath, video_id) "
            "VALUES (999, 'test_landmarks.npy', 999)"
        )
        
        # Insert test clip (frame 10 to 50, label class ID is 999)
        cur.execute(
            "INSERT INTO clips (id, start_frame_index, end_frame_index, video_id, gesture_class_id, gesture_type_id) "
            "VALUES (999, 10, 50, 999, 999, 999)"
        )
        
        conn.commit()
        print("PostgreSQL records seeded successfully.")
    except Exception as e:
        conn.rollback()
        print(f"PostgreSQL seeding failed: {e}")
        raise e
    finally:
        cur.close()
        conn.close()

    # 2. Generate and upload mock landmark .npy file to MinIO
    print("Generating mock MediaPipe Holistic landmarks...")
    # Generate 100 frames of 1629 holistic coordinates
    mock_landmarks = np.random.rand(100, 1629).astype(np.float32)
    
    # Save locally to upload
    temp_npy_path = "temp_test_landmarks.npy"
    np.save(temp_npy_path, mock_landmarks)
    
    print("Connecting to MinIO S3...")
    s3 = boto3.client(
        "s3",
        endpoint_url=S3_URL,
        region_name="us-east-1",
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
    )
    
    try:
        # Check and create bucket if not exists
        try:
            s3.head_bucket(Bucket=S3_BUCKET)
        except s3.exceptions.ClientError:
            print(f"Creating S3 Bucket '{S3_BUCKET}'...")
            s3.create_bucket(Bucket=S3_BUCKET)
            
        s3.upload_file(temp_npy_path, S3_BUCKET, "test_landmarks.npy")
        print("Mock landmark array uploaded to MinIO.")
    finally:
        if os.path.exists(temp_npy_path):
            os.remove(temp_npy_path)

def clean_database_records():
    """
    Cleans up mock test records from database.
    """
    import psycopg2
    print("\n--- Cleaning up seeded database records ---")
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM clips WHERE video_id = 999")
        cur.execute("DELETE FROM landmarks WHERE video_id = 999")
        cur.execute("DELETE FROM videos WHERE id = 999")
        cur.execute("DELETE FROM datasets WHERE id = 999")
        cur.execute("DELETE FROM gesture_classes WHERE id = 999")
        cur.execute("DELETE FROM gesture_types WHERE id = 999")
        conn.commit()
        print("Database cleaned up successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Cleanup failed: {e}")
    finally:
        cur.close()
        conn.close()

def run_integration_test():
    # 1. Seed mock database and S3 data
    try:
        seed_database_and_s3()
    except Exception as e:
        print(f"Failed to seed data: {e}")
        return

    # 2. Run DataLoader from Backend
    print("\n--- Testing get_backend_dataloader ---")
    
    # We use a custom local directory to avoid pollution
    cache_dir = Path(__file__).parent.parent / "data" / "dataset_999"
    
    try:
        # Create a FeatureEnhancer for data pipeline
        enhancer = FeatureEnhancer(
            use_relative_hands=True,
            use_distances=True,
            use_velocities=True,
            select_keypoints=True
        )

        # Trigger download and load
        dataloader = get_backend_dataloader(
            dataset_id=999,
            backend_url=BACKEND_URL,
            dest_dir=cache_dir,
            batch_size=2,
            shuffle=False,
            num_frames=30, # slice to 30 frames
            transform=enhancer
        )

        print("\nDataLoader returned successfully. Fetching batch...")
        for batch_idx, (landmarks, labels) in enumerate(dataloader):
            print(f"Batch {batch_idx + 1}:")
            print(f" - Landmarks shape: {landmarks.shape} (Expected: [1, 30, 352])")
            print(f" - Labels shape: {labels.shape}")
            print(f" - Labels values: {labels.tolist()}")
            
            # Assert correct shapes (only 1 clip in our test dataset)
            assert list(landmarks.shape) == [1, 30, 352], f"Expected shape [1, 30, 352], got {list(landmarks.shape)}"
            assert list(labels.shape) == [1], f"Expected label shape [1], got {list(labels.shape)}"
            print("\n>>> INTEGRATION TEST PASSED SUCCESSFULLY! <<<")
            break
            
    except Exception as e:
        print(f"\n>>> INTEGRATION TEST FAILED: {e} <<<")
    finally:
        # Clean up database records
        clean_database_records()
        
        # Clean up local cache directory
        if cache_dir.exists():
            import shutil
            shutil.rmtree(cache_dir)
            print("Local cache directory cleaned up.")

if __name__ == "__main__":
    run_integration_test()
