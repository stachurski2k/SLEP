import os
import logging
import asyncio
import numpy as np
from app.workers.celery_app import celery_app
from app.services.s3 import S3Service
from app.services.landmark_extraction import LandmarkExtractionService
from app.db.database import AsyncSessionLocal
from app.crud.video import VideoCrud
from app.core.config import config

logger = logging.getLogger(__name__)


def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task(bind=True, max_retries=3)
def process_video(self, video_id: int):
    local_path = None
    local_npy_path = None

    try:
        logger.info(f"Starting task for video {video_id}")
        s3_service = S3Service()
        landmark_service = LandmarkExtractionService()

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

        # 2. Extract landmarks using the dedicated service
        logger.info(f"Video {video_id}: Extracting landmarks...")
        landmarks_array = landmark_service.extract_from_video(local_path)

        # 3. Save as .npy
        npy_filename = f"{os.path.splitext(os.path.basename(video.filepath))[0]}_landmarks.npy"
        local_npy_path = f"{config.tmp_dir}/{npy_filename}"
        np.save(local_npy_path, landmarks_array)

        logger.info(
            f"Video {video_id}: Saved landmarks array "
            f"shape={landmarks_array.shape} to {local_npy_path}"
        )

        # 4. Upload the .npy file to S3
        s3_key = npy_filename
        s3_service.upload(local_npy_path, s3_key)

        # 5. Save landmark data in the database
        async def _add_landmark():
            async with AsyncSessionLocal() as session:
                try:
                    crud = VideoCrud(session)
                    await crud.add_landmark(video_id, s3_key)
                    await session.commit()
                except Exception as e:
                    await session.rollback()
                    raise e
                    
        run_async(_add_landmark())

        return s3_key

    except Exception as exc:
        logger.error(f"Error processing video {video_id}: {exc}")
        raise self.retry(exc=exc, countdown=5)

    finally:
        if local_path and os.path.exists(local_path):
            os.remove(local_path)
        if local_npy_path and os.path.exists(local_npy_path):
            os.remove(local_npy_path)