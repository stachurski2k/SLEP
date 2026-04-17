import csv
import os
import logging
import asyncio
import imageio
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
from app.workers.celery_app import celery_app
from app.services.s3 import S3Service
from app.db.database import AsyncSessionLocal
from app.crud.video import VideoCrud
from app.core.config import config

logger = logging.getLogger(__name__)


def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task(bind=True, max_retries=3)
def process_video(self, video_id: int):
    local_path = None
    local_csv_path = None

    try:
        logger.info(f"Starting task for video {video_id}")
        s3_service = S3Service()

        # 1. Database & Download (Keep async logic isolated)
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

        # 2. MediaPipe Initialization (MUST BE INSIDE THE TASK)
        base_options = mp_python.BaseOptions(model_asset_path='/app/models/hand_landmarker.task')
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_hands=2
        )

        all_landmarks_data = []

        # 'with' ensures the C++ graph is destroyed correctly even if it crashes
        with vision.HandLandmarker.create_from_options(options) as detector:
            reader = imageio.get_reader(local_path)

            for frame_idx, frame in enumerate(reader):
                # Wrap in mp.Image
                mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)

                # Perform detection
                result = detector.detect(mp_frame)

                if result.hand_landmarks:
                    for hand_idx, hand_landmarks in enumerate(result.hand_landmarks):
                        for lm_idx, lm in enumerate(hand_landmarks):
                            all_landmarks_data.append([
                                frame_idx, hand_idx, lm_idx, lm.x, lm.y, lm.z
                            ])

                if frame_idx % 10 == 0:
                    logger.info(f"Video {video_id}: Processed {frame_idx} frames")

            reader.close()

        # 3. CSV Creation
        csv_filename = f"{os.path.splitext(os.path.basename(video.filepath))[0]}_landmarks.csv"
        local_csv_path = f"{config.tmp_dir}/{csv_filename}"

        with open(local_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['frame_idx', 'hand_idx', 'landmark_idx', 'x', 'y', 'z'])
            writer.writerows(all_landmarks_data)

        # 4. Upload & Cleanup
        s3_key = f"{csv_filename}"
        s3_service.upload(local_csv_path, s3_key)

        return s3_key

    except Exception as exc:
        logger.error(f"Error processing video {video_id}: {exc}")
        raise self.retry(exc=exc, countdown=5)

    finally:
        # Final cleanup to ensure Docker doesn't run out of space
        if local_path and os.path.exists(local_path):
            os.remove(local_path)
        if local_csv_path and os.path.exists(local_csv_path):
            os.remove(local_csv_path)