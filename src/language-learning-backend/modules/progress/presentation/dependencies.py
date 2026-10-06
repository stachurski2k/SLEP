from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db

from modules.statistics.infrastructure.repositories import (
    PostgresDailyActivityRepository,
)
from ..application.interfaces import ProgressApplicationService
from ..application.services import ProgressApplicationServiceImpl
from ..infrastructure.repositories import (
    PostgresLessonProgressRepository,
    PostgresUserProgressRepository,
)


def get_progress_service(
    db: AsyncSession = Depends(get_db),
) -> ProgressApplicationService:
    user_progress_repo = PostgresUserProgressRepository(session=db)
    lesson_progress_repo = PostgresLessonProgressRepository(session=db)
    daily_activity_repo = PostgresDailyActivityRepository(session=db)
    return ProgressApplicationServiceImpl(
        user_progress_repository=user_progress_repo,
        lesson_progress_repository=lesson_progress_repo,
        daily_activity_repository=daily_activity_repo,
    )
