from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..domain.entities import Course, Exercise, Lesson, Unit
from ..domain.repositories import (
    CourseRepository,
    ExerciseRepository,
    LessonRepository,
    UnitRepository,
)
from ..domain.value_objects import ContentStatus, Difficulty, SignLanguage
from .mappers import LearningMapper
from .models import CourseModel, ExerciseModel, LessonModel, MediaModel, UnitModel


class PostgresCourseRepository(CourseRepository):
    """SQLAlchemy implementation of CourseRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, course_id: UUID) -> Course | None:
        stmt = (
            select(CourseModel)
            .options(selectinload(CourseModel.units).selectinload(UnitModel.lessons))
            .where(CourseModel.id == course_id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return LearningMapper.course_to_domain(model) if model else None

    async def list_all(
        self,
        language: SignLanguage | None = None,
        difficulty: Difficulty | None = None,
        status: ContentStatus | None = None,
    ) -> list[Course]:
        stmt = select(CourseModel).options(selectinload(CourseModel.units))

        if language:
            stmt = stmt.where(CourseModel.language == language.value)
        if difficulty:
            stmt = stmt.where(CourseModel.difficulty == difficulty.value)
        if status:
            stmt = stmt.where(CourseModel.status == status.value)

        stmt = stmt.order_by(CourseModel.created_at.desc())
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [LearningMapper.course_to_domain(m) for m in models]

    async def save(self, course: Course) -> None:
        stmt = select(CourseModel).where(CourseModel.id == course.id)
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            model = LearningMapper.course_to_persistence(course)
            self._session.add(model)
        else:
            LearningMapper.course_to_persistence(course, existing_model=existing)

        await self._session.flush()

    async def delete(self, course_id: UUID) -> None:
        stmt = delete(CourseModel).where(CourseModel.id == course_id)
        await self._session.execute(stmt)
        await self._session.flush()


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

    async def list_by_course(self, course_id: UUID) -> list[Unit]:
        stmt = (
            select(UnitModel)
            .options(selectinload(UnitModel.lessons))
            .where(UnitModel.course_id == course_id)
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
