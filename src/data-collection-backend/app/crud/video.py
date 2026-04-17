# app/crud/video.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload

from app.models import Landmark
from app.models.video import Video
from app.models.clip import Clip
from app.schemas.clip import ClipSchema
from app.schemas.landmark import LandmarkSchema
from app.schemas.video import VideoSchema, VideoSummarySchema


class VideoCrud:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_video(self, name: str, filepath: str) -> VideoSummarySchema:
        video = Video(name=name, filepath=filepath)
        self.db.add(video)
        await self.db.flush()
        await self.db.refresh(video)
        return VideoSummarySchema.model_validate(video)

    async def read_video(self, video_id: int) -> VideoSchema | None:
        result = await self.db.execute(
            select(Video)
            .where(Video.id == video_id)
            .options(
                selectinload(Video.landmarks),
                selectinload(Video.clips).options(
                    joinedload(Clip.gesture_class),
                    joinedload(Clip.gesture_type),
                ),
            )
        )
        video = result.scalar_one_or_none()
        if not video:
            return None
        return VideoSchema.model_validate(video)


    async def read_videos(self, page: int = 0, limit: int = 100) -> list[VideoSummarySchema]:
        result = await self.db.execute(
            select(Video.id, Video.name, Video.filepath)
            .offset(page * limit)
            .limit(limit)
        )
        return [VideoSummarySchema.model_validate(row) for row in result.mappings().all()]

    async def delete_video(self, video_id: int) -> bool:
        video = await self.db.get(Video, video_id)
        if not video:
            return False
        await self.db.delete(video)
        await self.db.flush()
        return True


    async def add_landmark(self, video_id: int, filepath: str) -> LandmarkSchema | None:
        video = await self.db.get(Video, video_id)
        if not video:
            return None

        landmark = Landmark(filepath=filepath, video_id=video_id)
        self.db.add(landmark)
        await self.db.flush()
        await self.db.refresh(landmark)
        return LandmarkSchema.model_validate(landmark)

    async def delete_landmark(self, landmark_id: int) -> bool:
        landmark = await self.db.get(Landmark, landmark_id)
        if not landmark:
            return False
        await self.db.delete(landmark)
        await self.db.flush()
        return True

    async def add_clip(
            self,
            video_id: int,
            start_frame_index: int,
            end_frame_index: int,
            gesture_class_id: int,
            gesture_type_id: int,
    ) -> ClipSchema | None:
        video = await self.db.get(Video, video_id)
        if not video:
            return None

        clip = Clip(
            video_id=video_id,
            start_frame_index=start_frame_index,
            end_frame_index=end_frame_index,
            gesture_class_id=gesture_class_id,
            gesture_type_id=gesture_type_id,
        )
        self.db.add(clip)
        await self.db.flush()

        # reload with relationships so Pydantic can serialize gesture_class and gesture_type
        result = await self.db.execute(
            select(Clip)
            .where(Clip.id == clip.id)
            .options(
                joinedload(Clip.gesture_class),
                joinedload(Clip.gesture_type),
            )
        )
        clip = result.scalar_one()
        return ClipSchema.model_validate(clip)

    async def update_clip(
            self,
            clip_id: int,
            start_frame_index: int | None = None,
            end_frame_index: int | None = None,
            gesture_class_id: int | None = None,
            gesture_type_id: int | None = None,
    ) -> ClipSchema | None:
        result = await self.db.execute(
            select(Clip)
            .where(Clip.id == clip_id)
            .options(
                joinedload(Clip.gesture_class),
                joinedload(Clip.gesture_type),
            )
        )
        clip = result.scalar_one_or_none()
        if not clip:
            return None

        if start_frame_index is not None:
            clip.start_frame_index = start_frame_index
        if end_frame_index is not None:
            clip.end_frame_index = end_frame_index
        if gesture_class_id is not None:
            clip.gesture_class_id = gesture_class_id
        if gesture_type_id is not None:
            clip.gesture_type_id = gesture_type_id

        await self.db.flush()

        # reload after update to get fresh relationship data
        result = await self.db.execute(
            select(Clip)
            .where(Clip.id == clip_id)
            .options(
                joinedload(Clip.gesture_class),
                joinedload(Clip.gesture_type),
            )
        )
        clip = result.scalar_one()
        return ClipSchema.model_validate(clip)

    async def delete_clip(self, clip_id: int) -> bool:
        clip = await self.db.get(Clip, clip_id)
        if not clip:
            return False
        await self.db.delete(clip)
        await self.db.flush()
        return True