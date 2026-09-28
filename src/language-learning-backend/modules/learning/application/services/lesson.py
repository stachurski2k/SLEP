from uuid import UUID, uuid4

from ...domain.entities import Lesson
from ...domain.exceptions import LessonNotFoundError, UnitNotFoundError
from ...domain.repositories import ExerciseRepository, LessonRepository, UnitRepository
from ...domain.value_objects import ContentStatus
from ..commands import CreateLessonCommand, UpdateLessonCommand
from ..dtos import ExercisePublicDTO, LessonDetailsDTO, LessonDTO, MediaDTO
from ..interfaces import LessonApplicationService


class LessonApplicationServiceImpl(LessonApplicationService):
    """Implementation of LessonApplicationService."""

    def __init__(
        self,
        lesson_repository: LessonRepository,
        unit_repository: UnitRepository,
        exercise_repository: ExerciseRepository,
    ) -> None:
        self._lesson_repo = lesson_repository
        self._unit_repo = unit_repository
        self._exercise_repo = exercise_repository

    async def createLesson(self, command: CreateLessonCommand) -> LessonDTO:
        unit = await self._unit_repo.get_by_id(command.unitId)
        if unit is None:
            raise UnitNotFoundError(f"Unit with ID '{command.unitId}' not found.")

        lesson = Lesson(
            id=uuid4(),
            unitId=command.unitId,
            title=command.title.strip(),
            description=command.description.strip(),
            order=command.order,
            status=ContentStatus.DRAFT,
        )
        await self._lesson_repo.save(lesson)
        return self._to_dto(lesson)

    async def updateLesson(self, command: UpdateLessonCommand) -> LessonDTO:
        lesson = await self._lesson_repo.get_by_id(command.lessonId)
        if lesson is None:
            raise LessonNotFoundError(f"Lesson with ID '{command.lessonId}' not found.")

        lesson.title = command.title.strip()
        lesson.description = command.description.strip()
        lesson.reorder(command.order)
        await self._lesson_repo.save(lesson)
        return self._to_dto(lesson)

    async def publishLesson(self, lesson_id: UUID) -> LessonDTO:
        lesson = await self._lesson_repo.get_by_id(lesson_id)
        if lesson is None:
            raise LessonNotFoundError(f"Lesson with ID '{lesson_id}' not found.")

        lesson.publish()
        await self._lesson_repo.save(lesson)
        return self._to_dto(lesson)

    async def deleteLesson(self, lesson_id: UUID) -> None:
        lesson = await self._lesson_repo.get_by_id(lesson_id)
        if lesson is None:
            raise LessonNotFoundError(f"Lesson with ID '{lesson_id}' not found.")
        await self._lesson_repo.delete(lesson_id)

    async def getLesson(self, lesson_id: UUID) -> LessonDTO | None:
        lesson = await self._lesson_repo.get_by_id(lesson_id)
        return self._to_dto(lesson) if lesson else None

    async def getLessonDetails(self, lesson_id: UUID) -> LessonDetailsDTO | None:
        lesson = await self._lesson_repo.get_by_id(lesson_id)
        if lesson is None:
            return None

        exercises = await self._exercise_repo.list_by_lesson(lesson.id)
        exercises_dto = [
            ExercisePublicDTO(
                id=e.id,
                lessonId=e.lessonId,
                type=e.type.value,
                difficulty=e.difficulty.value,
                points=e.points,
                content=e.content,
                media=[
                    MediaDTO(
                        id=m.id,
                        exerciseId=m.exerciseId,
                        type=m.type.value,
                        url=m.url,
                    )
                    for m in e.media
                ],
            )
            for e in exercises
        ]

        return LessonDetailsDTO(
            id=lesson.id,
            unitId=lesson.unitId,
            title=lesson.title,
            description=lesson.description,
            order=lesson.order,
            status=lesson.status.value,
            exercises=exercises_dto,
        )

    async def getLessonsByUnit(self, unit_id: UUID) -> list[LessonDTO]:
        lessons = await self._lesson_repo.list_by_unit(unit_id)
        return [self._to_dto(l) for l in lessons]

    @staticmethod
    def _to_dto(lesson: Lesson) -> LessonDTO:
        return LessonDTO(
            id=lesson.id,
            unitId=lesson.unitId,
            title=lesson.title,
            description=lesson.description,
            order=lesson.order,
            status=lesson.status.value,
        )
