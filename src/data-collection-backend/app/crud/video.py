from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.video import Video
from app.models.clip import Clip
from app.models.landmarks import Landmark
from app.schemas.video import VideoSchema, VideoSummarySchema
from app.schemas.clip import ClipSchema
from app.schemas.landmark import LandmarkSchema


class VideoCrud:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Video
    # ------------------------------------------------------------------

    async def create(
        self,
        name: str,
        filepath: str,
        description: str = "",
        fps: int = 0,
        total_length_seconds: float = 0,
        dataset_id: int | None = None,
    ) -> VideoSummarySchema:
        video = Video(
            name=name,
            filepath=filepath,
            description=description,
            fps=fps,
            total_length_seconds=total_length_seconds,
            dataset_id=dataset_id,
        )
        self.db.add(video)
        await self.db.flush()
        await self.db.refresh(video)
        return VideoSummarySchema.model_validate(video)

    async def read(self, video_id: int) -> VideoSchema | None:
        result = await self.db.execute(
            select(Video)
            .options(
                selectinload(Video.landmarks),
                selectinload(Video.clips).options(
                    selectinload(Clip.gesture_class),
                    selectinload(Clip.gesture_type),
                ),
            )
            .where(Video.id == video_id)
        )
        video = result.scalar_one_or_none()
        if not video:
            return None
        return VideoSchema.model_validate(video)

    async def read_list(
        self,
        page: int = 0,
        limit: int = 100,
        dataset_id: int | None = None,
    ) -> list[VideoSummarySchema]:
        query = select(Video)
        if dataset_id is not None:
            query = query.where(Video.dataset_id == dataset_id)
        result = await self.db.execute(query.offset(page * limit).limit(limit))
        return [VideoSummarySchema.model_validate(row) for row in result.scalars().all()]

    async def update(
        self,
        video_id: int,
        name: str,
        description: str,
        fps: int,
        total_length_seconds: float,
        dataset_id: int | None = None,
    ) -> VideoSummarySchema | None:
        video = await self.db.get(Video, video_id)
        if not video:
            return None
        video.name = name
        video.description = description
        video.fps = fps
        video.total_length_seconds = total_length_seconds
        video.dataset_id = dataset_id
        await self.db.flush()
        await self.db.refresh(video)
        return VideoSummarySchema.model_validate(video)

    async def delete(self, video_id: int) -> bool:
        video = await self.db.get(Video, video_id)
        if not video:
            return False
        await self.db.delete(video)
        await self.db.flush()
        return True

    # ------------------------------------------------------------------
    # Clips (managed through video as aggregate root)
    # ------------------------------------------------------------------

    async def read_clips(
        self,
        video_id: int,
        gesture_class_id: int | None = None,
        gesture_type_id: int | None = None,
    ) -> list[ClipSchema]:
        query = (
            select(Clip)
            .options(
                selectinload(Clip.gesture_class),
                selectinload(Clip.gesture_type),
            )
            .where(Clip.video_id == video_id)
        )
        if gesture_class_id is not None:
            query = query.where(Clip.gesture_class_id == gesture_class_id)
        if gesture_type_id is not None:
            query = query.where(Clip.gesture_type_id == gesture_type_id)
        result = await self.db.execute(query)
        return [ClipSchema.model_validate(row) for row in result.scalars().all()]

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
        result = await self.db.execute(
            select(Clip)
            .options(
                selectinload(Clip.gesture_class),
                selectinload(Clip.gesture_type),
            )
            .where(Clip.id == clip.id)
        )
        return ClipSchema.model_validate(result.scalar_one())

    async def update_clip(
        self,
        clip_id: int,
        start_frame_index: int,
        end_frame_index: int,
        gesture_class_id: int,
        gesture_type_id: int,
    ) -> ClipSchema | None:
        clip = await self.db.get(Clip, clip_id)
        if not clip:
            return None
        clip.start_frame_index = start_frame_index
        clip.end_frame_index = end_frame_index
        clip.gesture_class_id = gesture_class_id
        clip.gesture_type_id = gesture_type_id
        await self.db.flush()
        result = await self.db.execute(
            select(Clip)
            .options(
                selectinload(Clip.gesture_class),
                selectinload(Clip.gesture_type),
            )
            .where(Clip.id == clip_id)
        )
        return ClipSchema.model_validate(result.scalar_one())

    async def delete_clip(self, clip_id: int) -> bool:
        clip = await self.db.get(Clip, clip_id)
        if not clip:
            return False
        await self.db.delete(clip)
        await self.db.flush()
        return True

    # ------------------------------------------------------------------
    # Landmarks (managed through video as aggregate root)
    # ------------------------------------------------------------------

    async def read_landmarks(self, video_id: int) -> list[LandmarkSchema]:
        result = await self.db.execute(
            select(Landmark).where(Landmark.video_id == video_id)
        )
        return [LandmarkSchema.model_validate(row) for row in result.scalars().all()]

    async def add_landmark(
        self,
        video_id: int,
        filepath: str,
        landmark_on_video_preview_path: str | None = None,
    ) -> LandmarkSchema | None:
        video = await self.db.get(Video, video_id)
        if not video:
            return None
        landmark = Landmark(
            video_id=video_id,
            filepath=filepath,
            landmark_on_video_preview_path=landmark_on_video_preview_path,
        )
        self.db.add(landmark)
        await self.db.flush()
        await self.db.refresh(landmark)
        return LandmarkSchema.model_validate(landmark)

    async def update_landmark(
        self,
        landmark_id: int,
        landmark_on_video_preview_path: str | None,
    ) -> LandmarkSchema | None:
        landmark = await self.db.get(Landmark, landmark_id)
        if not landmark:
            return None
        landmark.landmark_on_video_preview_path = landmark_on_video_preview_path
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
