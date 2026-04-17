# app/api/v1/video.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.crud.video import VideoCrud
from app.schemas.clip import ClipSchema, ClipCreateSchema
from app.schemas.landmark import LandmarkSchema
from app.services.video import VideoService
from app.schemas.video import VideoSchema, VideoSummarySchema

router = APIRouter(prefix="/videos", tags=["videos"])

@router.post("/", response_model=VideoSchema)
async def create_video(name: str, filepath: str, db: AsyncSession = Depends(get_db)):
    return await VideoService(db).create_video(name, filepath)

@router.get("/", response_model=list[VideoSummarySchema])
async def list_videos(page: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await VideoCrud(db).read_videos(page, limit)

@router.get("/{video_id}", response_model=VideoSchema)
async def get_video(video_id: int, db: AsyncSession = Depends(get_db)):
    video = await VideoCrud(db).read_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video

@router.delete("/{video_id}", status_code=204)
async def delete_video(video_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await VideoCrud(db).delete_video(video_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Video not found")

@router.post("/{video_id}/landmarks", response_model=LandmarkSchema)
async def add_landmark(video_id: int, filepath: str, db: AsyncSession = Depends(get_db)):
    landmark = await VideoCrud(db).add_landmark(video_id, filepath)
    if not landmark:
        raise HTTPException(status_code=404, detail="Video not found")
    return landmark

@router.delete("/landmarks/{landmark_id}", status_code=204)
async def delete_landmark(landmark_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await VideoCrud(db).delete_landmark(landmark_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Landmark not found")

# clips
@router.post("/{video_id}/clips", response_model=ClipSchema)
async def add_clip(video_id: int, body: ClipCreateSchema, db: AsyncSession = Depends(get_db)):
    clip = await VideoCrud(db).add_clip(video_id, **body.model_dump())
    if not clip:
        raise HTTPException(status_code=404, detail="Video not found")
    return clip

@router.delete("/clips/{clip_id}", status_code=204)
async def delete_clip(clip_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await VideoCrud(db).delete_clip(clip_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Clip not found")