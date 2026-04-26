from pydantic import BaseModel


class ImportVideoJobCreateRequest(BaseModel):
    video_name: str
    video_filepath: str
    video_description: str
    dataset_id: int | None = None
