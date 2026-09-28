from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db

from ..application.interfaces import (
    CourseApplicationService,
    ExerciseApplicationService,
    LessonApplicationService,
    UnitApplicationService,
)
from ..application.services import (
    CourseApplicationServiceImpl,
    ExerciseApplicationServiceImpl,
    LessonApplicationServiceImpl,
    UnitApplicationServiceImpl,
)
from ..infrastructure.repositories import (
    PostgresCourseRepository,
    PostgresExerciseRepository,
    PostgresLessonRepository,
    PostgresUnitRepository,
)


def get_course_service(
    db: AsyncSession = Depends(get_db),
) -> CourseApplicationService:
    course_repo = PostgresCourseRepository(session=db)
    unit_repo = PostgresUnitRepository(session=db)
    lesson_repo = PostgresLessonRepository(session=db)
    return CourseApplicationServiceImpl(
        course_repository=course_repo,
        unit_repository=unit_repo,
        lesson_repository=lesson_repo,
    )


def get_unit_service(
    db: AsyncSession = Depends(get_db),
) -> UnitApplicationService:
    unit_repo = PostgresUnitRepository(session=db)
    course_repo = PostgresCourseRepository(session=db)
    return UnitApplicationServiceImpl(
        unit_repository=unit_repo,
        course_repository=course_repo,
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
