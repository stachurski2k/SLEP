from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.videos.schemas import (
    ClipRequest,
    LandmarkCreateRequest,
    LandmarkUpdateRequest,
    VideoCreateRequest,
    VideoUpdateRequest,
)
from app.crud.video import VideoCrud
from app.dependencies import get_db
from app.schemas.clip import ClipSchema
from app.schemas.landmark import LandmarkSchema
from app.schemas.video import VideoSchema, VideoSummarySchema

router = APIRouter(prefix="/videos", tags=["videos"])


# ------------------------------------------------------------------
# Video
# ------------------------------------------------------------------
@router.get("/", response_model=list[VideoSummarySchema])
async def list_videos(
    page: int = 0,
    limit: int = 100,
    dataset_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await VideoCrud(db).read_list(page, limit, dataset_id)


@router.get("/{video_id}", response_model=VideoSchema)
async def get_video(video_id: int, db: AsyncSession = Depends(get_db)):
    result = await VideoCrud(db).read(video_id)
    if not result:
        raise HTTPException(status_code=404, detail="Video not found")
    return result


@router.patch("/{video_id}", response_model=VideoSummarySchema)
async def update_video(video_id: int, body: VideoUpdateRequest, db: AsyncSession = Depends(get_db)):
    result = await VideoCrud(db).update(video_id, body.name, body.description, body.fps, body.total_length_seconds, body.dataset_id)
    if not result:
        raise HTTPException(status_code=404, detail="Video not found")
    return result


@router.delete("/{video_id}", status_code=204)
async def delete_video(video_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await VideoCrud(db).delete(video_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Video not found")


# ------------------------------------------------------------------
# Clips
# ------------------------------------------------------------------

@router.get("/{video_id}/clips", response_model=list[ClipSchema])
async def list_clips(
    video_id: int,
    gesture_class_id: int | None = None,
    gesture_type_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await VideoCrud(db).read_clips(video_id, gesture_class_id, gesture_type_id)


@router.post("/{video_id}/clips", response_model=ClipSchema)
async def add_clip(video_id: int, body: ClipRequest, db: AsyncSession = Depends(get_db)):
    result = await VideoCrud(db).add_clip(
        video_id,
        body.start_frame_index,
        body.end_frame_index,
        body.gesture_class_id,
        body.gesture_type_id,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Video not found")
    return result


@router.patch("/clips/{clip_id}", response_model=ClipSchema)
async def update_clip(clip_id: int, body: ClipRequest, db: AsyncSession = Depends(get_db)):
    result = await VideoCrud(db).update_clip(
        clip_id,
        body.start_frame_index,
        body.end_frame_index,
        body.gesture_class_id,
        body.gesture_type_id,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Clip not found")
    return result


@router.delete("/clips/{clip_id}", status_code=204)
async def delete_clip(clip_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await VideoCrud(db).delete_clip(clip_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Clip not found")


# ------------------------------------------------------------------
# Landmarks
# ------------------------------------------------------------------

@router.get("/{video_id}/landmarks", response_model=list[LandmarkSchema])
async def list_landmarks(video_id: int, db: AsyncSession = Depends(get_db)):
    return await VideoCrud(db).read_landmarks(video_id)


@router.post("/{video_id}/landmarks", response_model=LandmarkSchema)
async def add_landmark(video_id: int, body: LandmarkCreateRequest, db: AsyncSession = Depends(get_db)):
    result = await VideoCrud(db).add_landmark(
        video_id, body.filepath, body.landmark_on_video_preview_path
    )
    if not result:
        raise HTTPException(status_code=404, detail="Video not found")
    return result


@router.patch("/landmarks/{landmark_id}", response_model=LandmarkSchema)
async def update_landmark(landmark_id: int, body: LandmarkUpdateRequest, db: AsyncSession = Depends(get_db)):
    result = await VideoCrud(db).update_landmark(landmark_id, body.landmark_on_video_preview_path)
    if not result:
        raise HTTPException(status_code=404, detail="Landmark not found")
    return result


@router.delete("/landmarks/{landmark_id}", status_code=204)
async def delete_landmark(landmark_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await VideoCrud(db).delete_landmark(landmark_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Landmark not found")
