from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.import_video_job import ImportVideoJobStatusEnum


class ImportVideoJobSchema(BaseModel):
    id: int
    status: ImportVideoJobStatusEnum
    created_at: datetime
    updated_at: datetime
    video_name: str
    video_filepath: str
    video_description: str
    dataset_id: int | None
    error_message: str | None
    video_id: int | None

    model_config = ConfigDict(from_attributes=True)
