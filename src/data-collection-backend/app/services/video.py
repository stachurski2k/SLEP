from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.video import VideoCrud
from app.schemas.video import VideoSchema, VideoSummarySchema
from app.workers.tasks import process_video


class VideoService:
    def __init__(self, db: AsyncSession):
        self.crud = VideoCrud(db)

    async def create_video(self, name: str, filepath: str) -> VideoSummarySchema:
        video = await self.crud.create_video(name, filepath)

        process_video.delay(video_id = video.id)

        return video