import os
import logging
import asyncio
import numpy as np

from app.crud.import_video_job import ImportVideoJobCrud
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
def process_video(self, job_id: int):
    local_path = None
    local_npy_path = None

    try:
        logger.info(f"Starting task for video {job_id}")
        s3_service = S3Service()
        landmark_service = LandmarkExtractionService()

        # 1. Fetch video metadata from the database and download the file from S3
        async def _get_video_job():
            async with AsyncSessionLocal() as session:
                crud = ImportVideoJobCrud(session)
                video_job = await crud.read(job_id)
                if not video_job:
                    raise ValueError(f"Video job {job_id} not found")
                return video_job

        video_job = run_async(_get_video_job())
        local_path = f"{config.tmp_dir}/{os.path.basename(video_job.video_filepath)}"
        s3_service.download(video_job.video_filepath, local_path)

        # 2. Extract landmarks using the dedicated service
        logger.info(f"Video {job_id}: Extracting landmarks...")
        landmarks_array = landmark_service.extract_from_video(local_path)

        # 3. Save as .npy
        npy_filename = f"{os.path.splitext(os.path.basename(video_job.video_filepath))[0]}_landmarks.npy"
        local_npy_path = f"{config.tmp_dir}/{npy_filename}"
        np.save(local_npy_path, landmarks_array)

        logger.info(
            f"Video {job_id}: Saved landmarks array "
            f"shape={landmarks_array.shape} to {local_npy_path}"
        )

        # 4. Upload the .npy file to S3
        s3_key = npy_filename
        s3_service.upload(local_npy_path, s3_key)

        # 5. Save landmark data in the database
        async def _save_video():
            async with AsyncSessionLocal() as session:
                try:
                    crud = VideoCrud(session)
                    video = await crud.create(
                        video_job.video_name,
                        video_job.video_filepath,
                        video_job.video_description,
                        30,
                        10,
                        video_job.dataset_id
                    )
                    await crud.add_landmark(video.id,s3_key)
                    await session.commit()
                except Exception as e:
                    await session.rollback()
                    raise e
                    
        run_async(_save_video())

        return s3_key

    except Exception as exc:
        logger.error(f"Error processing video {job_id}: {exc}")
        raise self.retry(exc=exc, countdown=5)

    finally:
        if local_path and os.path.exists(local_path):
            os.remove(local_path)
        if local_npy_path and os.path.exists(local_npy_path):
            os.remove(local_npy_path)
