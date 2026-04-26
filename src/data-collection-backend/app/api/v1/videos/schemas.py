from pydantic import BaseModel


class VideoCreateRequest(BaseModel):
    name: str
    filepath: str
    description: str = ""
    fps: int = 0
    total_length_seconds: float = 0
    dataset_id: int | None = None


class VideoUpdateRequest(BaseModel):
    name: str
    description: str
    fps: int
    total_length_seconds: float
    dataset_id: int | None = None


class ClipRequest(BaseModel):
    start_frame_index: int
    end_frame_index: int
    gesture_class_id: int
    gesture_type_id: int


class LandmarkCreateRequest(BaseModel):
    filepath: str
    landmark_on_video_preview_path: str | None = None


class LandmarkUpdateRequest(BaseModel):
    landmark_on_video_preview_path: str | None
