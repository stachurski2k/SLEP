from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.entities import LessonProgress, UserProgress
from ..domain.repositories import LessonProgressRepository, UserProgressRepository
from .mappers import ProgressMapper
from .models import LessonProgressModel, UserProgressModel


class PostgresUserProgressRepository(UserProgressRepository):
    """SQLAlchemy PostgreSQL implementation of UserProgressRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: UUID) -> UserProgress | None:
        stmt = select(UserProgressModel).where(UserProgressModel.user_id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return ProgressMapper.to_domain_user(model) if model else None

    async def save(self, user_progress: UserProgress) -> None:
        stmt = select(UserProgressModel).where(
            (UserProgressModel.id == user_progress.id)
            | (UserProgressModel.user_id == user_progress.userId)
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            model = ProgressMapper.to_model_user(user_progress)
            self._session.add(model)
        else:
            existing.xp = user_progress.xp
            existing.updated_at = user_progress.updatedAt

        await self._session.flush()


class PostgresLessonProgressRepository(LessonProgressRepository):
    """SQLAlchemy PostgreSQL implementation of LessonProgressRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_and_lesson(
        self, user_id: UUID, lesson_id: UUID
    ) -> LessonProgress | None:
        stmt = select(LessonProgressModel).where(
            LessonProgressModel.user_id == user_id,
            LessonProgressModel.lesson_id == lesson_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return ProgressMapper.to_domain_lesson(model) if model else None

    async def list_by_user_id(self, user_id: UUID) -> list[LessonProgress]:
        stmt = select(LessonProgressModel).where(LessonProgressModel.user_id == user_id)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [ProgressMapper.to_domain_lesson(m) for m in models]

    async def list_completed_by_user_id(self, user_id: UUID) -> list[LessonProgress]:
        stmt = select(LessonProgressModel).where(
            LessonProgressModel.user_id == user_id,
            LessonProgressModel.completed.is_(True),
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [ProgressMapper.to_domain_lesson(m) for m in models]

    async def save(self, lesson_progress: LessonProgress) -> None:
        stmt = select(LessonProgressModel).where(
            (LessonProgressModel.id == lesson_progress.id)
            | (
                (LessonProgressModel.user_id == lesson_progress.userId)
                & (LessonProgressModel.lesson_id == lesson_progress.lessonId)
            )
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            model = ProgressMapper.to_model_lesson(lesson_progress)
            self._session.add(model)
        else:
            existing.completed = lesson_progress.completed
            existing.attempts = lesson_progress.attempts
            existing.completed_at = lesson_progress.completedAt
            existing.last_attempt_at = lesson_progress.lastAttemptAt

        await self._session.flush()

    async def delete(self, user_id: UUID, lesson_id: UUID) -> None:
        stmt = delete(LessonProgressModel).where(
            LessonProgressModel.user_id == user_id,
            LessonProgressModel.lesson_id == lesson_id,
        )
        await self._session.execute(stmt)
        await self._session.flush()
