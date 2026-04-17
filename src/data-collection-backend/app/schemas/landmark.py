# app/schemas/landmark.py
from pydantic import BaseModel, ConfigDict

class LandmarkSchema(BaseModel):
    id: int
    filepath: str

    model_config = ConfigDict(from_attributes=True)