# app/schemas/landmark.py
from pydantic import BaseModel, ConfigDict

class LandmarkSchema(BaseModel):
    id: int
    filepath: str
    landmark_on_video_preview_path: str | None

    model_config = ConfigDict(from_attributes=True)