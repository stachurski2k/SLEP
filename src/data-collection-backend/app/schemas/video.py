# app/schemas/video.py
from pydantic import BaseModel, ConfigDict
from app.schemas.clip import ClipSchema
from app.schemas.landmark import LandmarkSchema


class VideoSummarySchema(BaseModel):
    id: int
    name: str
    filepath: str

    model_config = ConfigDict(from_attributes=True)


class VideoSchema(BaseModel):
    id: int
    name: str
    filepath: str
    description: str
    fps: int
    total_length_seconds: float
    dataset_id: int | None
    landmarks: list[LandmarkSchema] = []
    clips: list[ClipSchema] = []

    model_config = ConfigDict(from_attributes=True)