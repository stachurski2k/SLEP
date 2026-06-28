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


@celery_app.task(bind=True, max_retries=3)
def export_dataset_task(self, job_id: int):
    import zipfile
    import tempfile
    import shutil
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    from app.models.export_dataset_job import ExportDatasetJobStatusEnum
    from app.crud.export_dataset_job import ExportDatasetJobCrud
    from app.crud.dataset import DatasetCrud
    from app.crud.exported_dataset import ExportedDatasetCrud
    from app.models.video import Video
    from app.models.clip import Clip

    local_zip_path = None
    temp_dir = None

    try:
        logger.info(f"Starting export dataset task for job {job_id}")
        s3_service = S3Service()

        # 1. Fetch export job and dataset details from DB
        async def _get_job_and_dataset():
            async with AsyncSessionLocal() as session:
                job_crud = ExportDatasetJobCrud(session)
                job = await job_crud.read(job_id)
                if not job:
                    raise ValueError(f"Export job {job_id} not found")
                
                # Update status to processing
                await job_crud.update_status(job_id, ExportDatasetJobStatusEnum.processing)
                await session.commit()
                
                # Fetch dataset
                dataset_crud = DatasetCrud(session)
                dataset = await dataset_crud.read(job.original_dataset_id)
                if not dataset:
                    raise ValueError(f"Dataset {job.original_dataset_id} not found")
                
                # Fetch all videos in dataset with landmarks and clips
                query = (
                    select(Video)
                    .options(
                        selectinload(Video.landmarks),
                        selectinload(Video.clips)
                    )
                    .where(Video.dataset_id == dataset.id)
                )
                result = await session.execute(query)
                videos = result.scalars().all()
                
                return job, dataset, list(videos)

        job, dataset, videos = run_async(_get_job_and_dataset())

        # Create temporary directory for landmarks inside config.tmp_dir
        os.makedirs(config.tmp_dir, exist_ok=True)
        temp_dir = tempfile.mkdtemp(dir=config.tmp_dir)
        exported_clips_count = 0
        video_count = len(videos)

        for video in videos:
            if not video.landmarks:
                logger.warning(f"Video {video.id} has no landmarks associated, skipping.")
                continue
            
            # Download landmarks .npy from S3
            landmark_record = video.landmarks[0]
            s3_key = landmark_record.filepath
            
            # Temporary path for video landmark file
            local_npy_temp_path = os.path.join(temp_dir, f"video_{video.id}_raw.npy")
            try:
                s3_service.download(s3_key, local_npy_temp_path)
                # Load with memory mapping to avoid high RAM usage
                landmarks_array = np.load(local_npy_temp_path, mmap_mode='r')
                
                # Slice and save each clip
                if video.clips:
                    for clip in video.clips:
                        start = clip.start_frame_index
                        end = clip.end_frame_index
                        
                        # Bound checking
                        if start < 0:
                            start = 0
                        if end >= len(landmarks_array):
                            end = len(landmarks_array) - 1
                        
                        # Force in-memory array copy to release the memmap handle after slicing
                        clip_landmarks = np.array(landmarks_array[start : end + 1])
                        clip_filename = f"{clip.gesture_class_id}_{video.id}_{clip.id}.npy"
                        clip_filepath = os.path.join(temp_dir, clip_filename)
                        np.save(clip_filepath, clip_landmarks)
                        exported_clips_count += 1
                else:
                    logger.info(f"Video {video.id} has no clips. Skipping exporting as no gesture label is present.")
                
                # Release memory mapped file handle explicitly
                if hasattr(landmarks_array, '_mmap') and landmarks_array._mmap is not None:
                    landmarks_array._mmap.close()
                del landmarks_array
            except Exception as e:
                logger.error(f"Failed to process landmarks for video {video.id}: {e}")
            finally:
                if os.path.exists(local_npy_temp_path):
                    try:
                        os.remove(local_npy_temp_path)
                    except Exception as e:
                        logger.warning(f"Could not remove temporary file {local_npy_temp_path}: {e}")

        if exported_clips_count == 0:
            raise ValueError("No clips were exported. The dataset is empty or videos have no clips.")

        # Zip the directory
        zip_filename = f"dataset_{dataset.id}_export_{job_id}.zip"
        local_zip_path = os.path.join(config.tmp_dir, zip_filename)
        
        with zipfile.ZipFile(local_zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith('.npy') and not file.endswith('_raw.npy'):
                        file_path = os.path.join(root, file)
                        zip_file.write(file_path, arcname=file)

        # Upload zip to S3
        s3_zip_key = f"exports/{zip_filename}"
        s3_service.upload(local_zip_path, s3_zip_key, content_type="application/zip")

        # Save exported dataset and update job status
        async def _save_export_results():
            async with AsyncSessionLocal() as session:
                exported_crud = ExportedDatasetCrud(session)
                exported_record = await exported_crud.create(
                    filepath=s3_zip_key,
                    videos_count=video_count,
                    original_dataset_id=dataset.id,
                    original_dataset_name=dataset.name,
                    original_dataset_description=dataset.description
                )
                
                job_crud = ExportDatasetJobCrud(session)
                await job_crud.update_status(
                    job_id=job_id,
                    status=ExportDatasetJobStatusEnum.done,
                    exported_dataset_id=exported_record.id
                )
                await session.commit()

        run_async(_save_export_results())
        logger.info(f"Export job {job_id} finished successfully. Exported {exported_clips_count} clips.")
        return s3_zip_key

    except Exception as exc:
        logger.error(f"Error exporting dataset job {job_id}: {exc}")
        
        # Update job status to error
        async def _set_error_status():
            async with AsyncSessionLocal() as session:
                job_crud = ExportDatasetJobCrud(session)
                await job_crud.update_status(
                    job_id=job_id,
                    status=ExportDatasetJobStatusEnum.error,
                    error_message=str(exc)
                )
                await session.commit()
        
        try:
            run_async(_set_error_status())
        except Exception as e:
            logger.error(f"Failed to update error status for job {job_id}: {e}")
            
        raise self.retry(exc=exc, countdown=5)

    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        if local_zip_path and os.path.exists(local_zip_path):
            os.remove(local_zip_path)

