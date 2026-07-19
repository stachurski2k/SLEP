from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.export_dataset_job import ExportDatasetJobCrud
from app.schemas.export_dataset_job import ExportDatasetJobSchema
from app.workers.tasks import export_dataset_task

class ExportDatasetService:
    def __init__(self, db: AsyncSession):
        self.crud = ExportDatasetJobCrud(db)

    async def create_export_job(self, original_dataset_id: int) -> ExportDatasetJobSchema:
        job = await self.crud.create(original_dataset_id)
        export_dataset_task.delay(job.id)
        return ExportDatasetJobSchema.model_validate(job)
