from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.import_video_job import ImportVideoJobCrud
from app.crud.video import VideoCrud
from app.schemas.import_video_job import ImportVideoJobSchema
from app.schemas.video import VideoSchema, VideoSummarySchema
from app.workers.tasks import process_video


class VideoService:
    def __init__(self, db: AsyncSession):
        self.import_crud = ImportVideoJobCrud(db)
        self.video_crud = VideoCrud(db)

    async def create_video_import_job(self, name: str, filepath: str, description: str,dataset_id: int|None) -> ImportVideoJobSchema:

        job = await self.import_crud.create(
            name,
            filepath,
            description,
            dataset_id
        )
        process_video.delay(job.id)

        return ImportVideoJobSchema.model_validate(job)