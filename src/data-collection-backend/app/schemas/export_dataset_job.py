from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.export_dataset_job import ExportDatasetJobStatusEnum


class ExportDatasetJobSchema(BaseModel):
    id: int
    original_dataset_id: int
    status: ExportDatasetJobStatusEnum
    created_at: datetime
    updated_at: datetime
    error_message: str | None
    exported_dataset_id: int | None

    model_config = ConfigDict(from_attributes=True)
