# app/schemas/gesture_type.py
from pydantic import BaseModel, ConfigDict

class GestureTypeSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)