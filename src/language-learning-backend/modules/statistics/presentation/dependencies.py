from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db

from modules.learning.infrastructure.repositories import (
    PostgresCourseRepository,
    PostgresLessonRepository,
)
from modules.progress.infrastructure.repositories import (
    PostgresLessonProgressRepository,
    PostgresUserProgressRepository,
)
from ..application.interfaces import StatisticsApplicationService
from ..application.services import StatisticsApplicationServiceImpl
from ..infrastructure.repositories import PostgresDailyActivityRepository


def get_statistics_service(
    db: AsyncSession = Depends(get_db),
) -> StatisticsApplicationService:
    daily_activity_repo = PostgresDailyActivityRepository(session=db)
    user_progress_repo = PostgresUserProgressRepository(session=db)
    lesson_progress_repo = PostgresLessonProgressRepository(session=db)
    course_repo = PostgresCourseRepository(session=db)
    lesson_repo = PostgresLessonRepository(session=db)

    return StatisticsApplicationServiceImpl(
        daily_activity_repository=daily_activity_repo,
        user_progress_repository=user_progress_repo,
        lesson_progress_repository=lesson_progress_repo,
        course_repository=course_repo,
        lesson_repository=lesson_repo,
    )
