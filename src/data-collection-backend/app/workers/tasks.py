import os
import logging
import asyncio
import imageio
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
from app.workers.celery_app import celery_app
from app.services.s3 import S3Service
from app.db.database import AsyncSessionLocal
from app.crud.video import VideoCrud
from app.core.config import config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Landmark counts per body component (MediaPipe Holistic)
# ---------------------------------------------------------------------------
NUM_POSE_LANDMARKS = 33
NUM_FACE_LANDMARKS = 478
NUM_HAND_LANDMARKS = 21  # per hand (left and right are stored separately)

# ---------------------------------------------------------------------------
# Per-frame row layout (all values are float32, order: x, y, z per landmark)
#
#   Columns 0   – 98   : POSE (33 landmarks × 3)
#   Columns 99  – 1532 : FACE (478 landmarks × 3)
#   Columns 1533– 1595 : LEFT HAND (21 landmarks × 3)
#   Columns 1596– 1658 : RIGHT HAND (21 landmarks × 3)
#
#   Total columns: 1659
# ---------------------------------------------------------------------------


# Slice helpers for extracting individual components from a loaded .npy array
# Usage: landmarks = np.load("video_landmarks.npy")  # shape: (num_frames, 1659)
POSE_SLICE       = slice(0,    99)    # landmarks[:, POSE_SLICE]       → (F, 99)
FACE_SLICE       = slice(99,   1533)  # landmarks[:, FACE_SLICE]       → (F, 1434)
LEFT_HAND_SLICE  = slice(1533, 1596)  # landmarks[:, LEFT_HAND_SLICE]  → (F, 63)
RIGHT_HAND_SLICE = slice(1596, 1659)  # landmarks[:, RIGHT_HAND_SLICE] → (F, 63)

LANDMARK_ROW_SIZE = (NUM_POSE_LANDMARKS + NUM_FACE_LANDMARKS + NUM_HAND_LANDMARKS * 2) * 3


def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _extract_landmarks(landmarks, expected_count: int) -> np.ndarray:
    """
    Flatten landmark coordinates (x, y, z) into a 1-D float32 array.
    If the component was not detected in this frame, returns zeros so that
    every frame row has a consistent, fixed length.

    Args:
        landmarks:      List of NormalizedLandmark objects, or None/empty.
        expected_count: Number of landmarks expected for this component.

    Returns:
        np.ndarray of shape (expected_count * 3,), dtype float32.
    """
    if landmarks:
        coords = [[lm.x, lm.y, lm.z] for lm in landmarks]
    else:
        coords = [[0.0, 0.0, 0.0]] * expected_count

    return np.array(coords, dtype=np.float32).flatten()


@celery_app.task(bind=True, max_retries=3)
def process_video(self, video_id: int):
    local_path = None
    local_npy_path = None

    try:
        logger.info(f"Starting task for video {video_id}")
        s3_service = S3Service()

        # 1. Fetch video metadata from the database and download the file from S3
        async def _get_video():
            async with AsyncSessionLocal() as session:
                crud = VideoCrud(session)
                video = await crud.read_video(video_id)
                if not video:
                    raise ValueError(f"Video {video_id} not found")
                return video

        video = run_async(_get_video())
        local_path = f"{config.tmp_dir}/{os.path.basename(video.filepath)}"
        s3_service.download(video.filepath, local_path)

        # 2. Initialise HolisticLandmarker (must be done inside the task process,
        #    not at module level, to avoid sharing C++ graph state across workers)
        base_options = mp_python.BaseOptions(
            model_asset_path='/app/models/holistic_landmarker.task'
        )
        options = vision.HolisticLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
        )

        # Each element is one frame row — a flat float32 array of length LANDMARK_ROW_SIZE.
        # Component order: [pose | face | left_hand | right_hand]
        # Missing components are represented as zeros (consistent shape guaranteed).
        all_frames_data = []

        # 'with' block ensures the underlying C++ graph is destroyed cleanly
        # even if an exception is raised mid-video
        with vision.HolisticLandmarker.create_from_options(options) as detector:
            reader = imageio.get_reader(local_path)

            for frame_idx, frame in enumerate(reader):
                mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
                result = detector.detect(mp_frame)

                pose_row       = _extract_landmarks(result.pose_landmarks,       NUM_POSE_LANDMARKS)
                face_row       = _extract_landmarks(result.face_landmarks,       NUM_FACE_LANDMARKS)
                left_hand_row  = _extract_landmarks(result.left_hand_landmarks,  NUM_HAND_LANDMARKS)
                right_hand_row = _extract_landmarks(result.right_hand_landmarks, NUM_HAND_LANDMARKS)

                # One row per frame, shape: (LANDMARK_ROW_SIZE,) = (1659,)
                frame_row = np.concatenate([pose_row, face_row, left_hand_row, right_hand_row])
                all_frames_data.append(frame_row)

                if frame_idx % 10 == 0:
                    logger.info(f"Video {video_id}: Processed {frame_idx} frames")

            reader.close()

        # 3. Stack all frame rows into a 2-D array and save as .npy
        #    Final shape: (num_frames, 1659)
        landmarks_array = np.array(all_frames_data, dtype=np.float32)

        npy_filename = f"{os.path.splitext(os.path.basename(video.filepath))[0]}_landmarks.npy"
        local_npy_path = f"{config.tmp_dir}/{npy_filename}"
        np.save(local_npy_path, landmarks_array)

        logger.info(
            f"Video {video_id}: Saved landmarks array "
            f"shape={landmarks_array.shape} to {local_npy_path}"
        )

        # 4. Upload the .npy file to S3 and clean up local copies in 'finally'
        s3_key = npy_filename
        s3_service.upload(local_npy_path, s3_key)

        return s3_key

    except Exception as exc:
        logger.error(f"Error processing video {video_id}: {exc}")
        raise self.retry(exc=exc, countdown=5)

    finally:
        if local_path and os.path.exists(local_path):
            os.remove(local_path)
        if local_npy_path and os.path.exists(local_npy_path):
            os.remove(local_npy_path)