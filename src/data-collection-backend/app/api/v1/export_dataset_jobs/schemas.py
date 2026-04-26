from pydantic import BaseModel


class ExportDatasetJobCreateRequest(BaseModel):
    original_dataset_id: int
