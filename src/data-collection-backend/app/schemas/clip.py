# app/schemas/clip.py
from pydantic import BaseModel, ConfigDict
from app.schemas.gesture_class import GestureClassSchema
from app.schemas.gesture_type import GestureTypeSchema


class ClipSchema(BaseModel):
    id: int
    start_frame_index: int
    end_frame_index: int
    gesture_class: GestureClassSchema
    gesture_type: GestureTypeSchema

    model_config = ConfigDict(from_attributes=True)

class ClipCreateSchema(BaseModel):
    start_frame_index: int
    end_frame_index: int
    gesture_class_id: int
    gesture_type_id: int