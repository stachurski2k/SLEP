# app/schemas/gesture_class.py
from pydantic import BaseModel, ConfigDict

class GestureClassSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)