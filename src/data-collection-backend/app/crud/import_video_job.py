from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.import_video_job import ImportVideoJob, ImportVideoJobStatusEnum
from app.schemas.import_video_job import ImportVideoJobSchema


class ImportVideoJobCrud:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        video_name: str,
        video_filepath: str,
        video_description: str,
        dataset_id: int | None = None,
    ) -> ImportVideoJobSchema:
        now = datetime.now(timezone.utc)
        job = ImportVideoJob(
            status=ImportVideoJobStatusEnum.in_queue,
            created_at=now,
            updated_at=now,
            video_name=video_name,
            video_filepath=video_filepath,
            video_description=video_description,
            dataset_id=dataset_id,
        )
        self.db.add(job)
        await self.db.flush()
        await self.db.refresh(job)
        return ImportVideoJobSchema.model_validate(job)

    async def read(self, job_id: int) -> ImportVideoJobSchema | None:
        result = await self.db.get(ImportVideoJob, job_id)
        if not result:
            return None
        return ImportVideoJobSchema.model_validate(result)

    async def read_list(self, page: int = 0, limit: int = 100) -> list[ImportVideoJobSchema]:
        result = await self.db.execute(
            select(ImportVideoJob)
            .offset(page * limit)
            .limit(limit)
        )
        return [ImportVideoJobSchema.model_validate(row) for row in result.scalars().all()]

    async def update_status(
        self,
        job_id: int,
        status: ImportVideoJobStatusEnum,
        error_message: str | None = None,
        video_id: int | None = None,
    ) -> ImportVideoJobSchema | None:
        job = await self.db.get(ImportVideoJob, job_id)
        if not job:
            return None
        job.status = status
        job.updated_at = datetime.now(timezone.utc)
        job.error_message = error_message
        job.video_id = video_id
        await self.db.flush()
        await self.db.refresh(job)
        return ImportVideoJobSchema.model_validate(job)

    async def delete(self, job_id: int) -> bool:
        job = await self.db.get(ImportVideoJob, job_id)
        if not job:
            return False
        await self.db.delete(job)
        await self.db.flush()
        return True
