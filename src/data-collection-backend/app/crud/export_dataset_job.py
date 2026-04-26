from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.export_dataset_job import ExportDatasetJob, ExportDatasetJobStatusEnum
from app.schemas.export_dataset_job import ExportDatasetJobSchema


class ExportDatasetJobCrud:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, original_dataset_id: int) -> ExportDatasetJobSchema:
        now = datetime.now(timezone.utc)
        job = ExportDatasetJob(
            original_dataset_id=original_dataset_id,
            status=ExportDatasetJobStatusEnum.in_queue,
            created_at=now,
            updated_at=now,
        )
        self.db.add(job)
        await self.db.flush()
        await self.db.refresh(job)
        return ExportDatasetJobSchema.model_validate(job)

    async def read(self, job_id: int) -> ExportDatasetJobSchema | None:
        result = await self.db.get(ExportDatasetJob, job_id)
        if not result:
            return None
        return ExportDatasetJobSchema.model_validate(result)

    async def read_list(self, page: int = 0, limit: int = 100) -> list[ExportDatasetJobSchema]:
        result = await self.db.execute(
            select(ExportDatasetJob)
            .offset(page * limit)
            .limit(limit)
        )
        return [ExportDatasetJobSchema.model_validate(row) for row in result.scalars().all()]

    async def update_status(
        self,
        job_id: int,
        status: ExportDatasetJobStatusEnum,
        error_message: str | None = None,
        exported_dataset_id: int | None = None,
    ) -> ExportDatasetJobSchema | None:
        job = await self.db.get(ExportDatasetJob, job_id)
        if not job:
            return None
        job.status = status
        job.updated_at = datetime.now(timezone.utc)
        job.error_message = error_message
        job.exported_dataset_id = exported_dataset_id
        await self.db.flush()
        await self.db.refresh(job)
        return ExportDatasetJobSchema.model_validate(job)

    async def delete(self, job_id: int) -> bool:
        job = await self.db.get(ExportDatasetJob, job_id)
        if not job:
            return False
        await self.db.delete(job)
        await self.db.flush()
        return True
