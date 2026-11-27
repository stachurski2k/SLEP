from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..domain.entities import Exercise, Lesson, Unit
from ..domain.repositories import (
    ExerciseRepository,
    LessonRepository,
    UnitRepository,
)
from .mappers import LearningMapper
from .models import ExerciseModel, LessonModel, MediaModel, UnitModel


class PostgresUnitRepository(UnitRepository):
    """SQLAlchemy implementation of UnitRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, unit_id: UUID) -> Unit | None:
        stmt = (
            select(UnitModel)
            .options(selectinload(UnitModel.lessons))
            .where(UnitModel.id == unit_id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return LearningMapper.unit_to_domain(model) if model else None

    async def list_all(self) -> list[Unit]:
        stmt = (
            select(UnitModel)
            .options(selectinload(UnitModel.lessons))
            .order_by(UnitModel.order_no.asc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [LearningMapper.unit_to_domain(m) for m in models]

    async def save(self, unit: Unit) -> None:
        stmt = select(UnitModel).where(UnitModel.id == unit.id)
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            model = LearningMapper.unit_to_persistence(unit)
            self._session.add(model)
        else:
            LearningMapper.unit_to_persistence(unit, existing_model=existing)

        await self._session.flush()

    async def delete(self, unit_id: UUID) -> None:
        stmt = delete(UnitModel).where(UnitModel.id == unit_id)
        await self._session.execute(stmt)
        await self._session.flush()


class PostgresLessonRepository(LessonRepository):
    """SQLAlchemy implementation of LessonRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, lesson_id: UUID) -> Lesson | None:
        stmt = (
            select(LessonModel)
            .options(
                selectinload(LessonModel.exercises).selectinload(ExerciseModel.media)
            )
            .where(LessonModel.id == lesson_id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return LearningMapper.lesson_to_domain(model) if model else None

    async def list_by_unit(self, unit_id: UUID) -> list[Lesson]:
        stmt = (
            select(LessonModel)
            .options(selectinload(LessonModel.exercises))
            .where(LessonModel.unit_id == unit_id)
            .order_by(LessonModel.order_no.asc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [LearningMapper.lesson_to_domain(m) for m in models]

    async def save(self, lesson: Lesson) -> None:
        stmt = select(LessonModel).where(LessonModel.id == lesson.id)
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            model = LearningMapper.lesson_to_persistence(lesson)
            self._session.add(model)
        else:
            LearningMapper.lesson_to_persistence(lesson, existing_model=existing)

        await self._session.flush()

    async def delete(self, lesson_id: UUID) -> None:
        stmt = delete(LessonModel).where(LessonModel.id == lesson_id)
        await self._session.execute(stmt)
        await self._session.flush()


class PostgresExerciseRepository(ExerciseRepository):
    """SQLAlchemy implementation of ExerciseRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, exercise_id: UUID) -> Exercise | None:
        stmt = (
            select(ExerciseModel)
            .options(selectinload(ExerciseModel.media))
            .where(ExerciseModel.id == exercise_id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return LearningMapper.exercise_to_domain(model) if model else None

    async def list_by_lesson(self, lesson_id: UUID) -> list[Exercise]:
        stmt = (
            select(ExerciseModel)
            .options(selectinload(ExerciseModel.media))
            .where(ExerciseModel.lesson_id == lesson_id)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [LearningMapper.exercise_to_domain(m) for m in models]

    async def save(self, exercise: Exercise) -> None:
        stmt = (
            select(ExerciseModel)
            .options(selectinload(ExerciseModel.media))
            .where(ExerciseModel.id == exercise.id)
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            model = LearningMapper.exercise_to_persistence(exercise)
            self._session.add(model)
        else:
            LearningMapper.exercise_to_persistence(exercise, existing_model=existing)
            # Synchronize media items if changed
            existing.media.clear()
            for m in exercise.media:
                existing.media.append(
                    MediaModel(
                        id=m.id,
                        exercise_id=exercise.id,
                        type=m.type.value,
                        url=m.url,
                    )
                )

        await self._session.flush()

    async def delete(self, exercise_id: UUID) -> None:
        stmt = delete(ExerciseModel).where(ExerciseModel.id == exercise_id)
        await self._session.execute(stmt)
        await self._session.flush()
