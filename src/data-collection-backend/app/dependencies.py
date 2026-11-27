from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import config
from app.crud.video import VideoCrud
from app.db.database import AsyncSessionLocal
from app.services.s3 import S3Service
from app.services.video import VideoService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_video_crud(db:AsyncSession = Depends(get_db)):
    return VideoCrud(db)

async def get_video_service(db: AsyncSession = Depends(get_db), crud: VideoCrud = Depends(get_video_crud)):
    return VideoService(db,crud)

async def get_s3(request: Request):
    return S3Service(public_url=config.s3_public_url or f"http://{request.url.hostname}:9000")
