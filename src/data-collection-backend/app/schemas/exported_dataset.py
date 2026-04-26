from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ExportedDatasetSchema(BaseModel):
    id: int
    filepath: str
    videos_count: int
    created_at: datetime
    original_dataset_id: int
    original_dataset_name: str
    original_dataset_description: str

    model_config = ConfigDict(from_attributes=True)
