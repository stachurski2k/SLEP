from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db

from ..application.interfaces import (
    ExerciseApplicationService,
    LessonApplicationService,
    UnitApplicationService,
)
from ..application.services import (
    ExerciseApplicationServiceImpl,
    LessonApplicationServiceImpl,
    UnitApplicationServiceImpl,
)
from ..infrastructure.repositories import (
    PostgresExerciseRepository,
    PostgresLessonRepository,
    PostgresUnitRepository,
)


def get_unit_service(
    db: AsyncSession = Depends(get_db),
) -> UnitApplicationService:
    unit_repo = PostgresUnitRepository(session=db)
    return UnitApplicationServiceImpl(
        unit_repository=unit_repo,
    )


def get_lesson_service(
    db: AsyncSession = Depends(get_db),
) -> LessonApplicationService:
    lesson_repo = PostgresLessonRepository(session=db)
    unit_repo = PostgresUnitRepository(session=db)
    exercise_repo = PostgresExerciseRepository(session=db)
    return LessonApplicationServiceImpl(
        lesson_repository=lesson_repo,
        unit_repository=unit_repo,
        exercise_repository=exercise_repo,
    )


def get_exercise_service(
    db: AsyncSession = Depends(get_db),
) -> ExerciseApplicationService:
    exercise_repo = PostgresExerciseRepository(session=db)
    lesson_repo = PostgresLessonRepository(session=db)
    return ExerciseApplicationServiceImpl(
        exercise_repository=exercise_repo,
        lesson_repository=lesson_repo,
    )
