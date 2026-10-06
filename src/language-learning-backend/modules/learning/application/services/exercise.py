from uuid import UUID, uuid4

from ...domain.entities import Exercise, Media
from ...domain.exceptions import ExerciseNotFoundError, LessonNotFoundError
from ...domain.repositories import ExerciseRepository, LessonRepository
from ...domain.value_objects import Difficulty, ExerciseType, MediaType
from ..commands import (
    CreateExerciseCommand,
    UpdateExerciseCommand,
    ValidateAnswerCommand,
)
from ..dtos import (
    ExercisePublicDTO,
    ValidationResultDTO,
)
from ..interfaces import ExerciseApplicationService


class ExerciseApplicationServiceImpl(ExerciseApplicationService):
    """Implementation of ExerciseApplicationService."""

    def __init__(
        self,
        exercise_repository: ExerciseRepository,
        lesson_repository: LessonRepository,
    ) -> None:
        self._exercise_repo = exercise_repository
        self._lesson_repo = lesson_repository

    async def createExercise(self, command: CreateExerciseCommand) -> Exercise:
        lesson = await self._lesson_repo.get_by_id(command.lessonId)
        if lesson is None:
            raise LessonNotFoundError(f"Lesson with ID '{command.lessonId}' not found.")

        type_vo = ExerciseType(command.type)
        difficulty_vo = Difficulty(command.difficulty)

        exercise_id = uuid4()
        media_entities = [
            Media(
                id=uuid4(),
                exerciseId=exercise_id,
                type=MediaType(m.type),
                url=m.url.strip(),
            )
            for m in command.mediaList
        ]

        exercise = Exercise(
            id=exercise_id,
            lessonId=command.lessonId,
            type=type_vo,
            difficulty=difficulty_vo,
            points=command.points,
            content=command.content.strip(),
            answer=command.answer.strip(),
            media=media_entities,
        )
        await self._exercise_repo.save(exercise)
        return exercise

    async def updateExercise(self, command: UpdateExerciseCommand) -> Exercise:
        exercise = await self._exercise_repo.get_by_id(command.exerciseId)
        if exercise is None:
            raise ExerciseNotFoundError(f"Exercise with ID '{command.exerciseId}' not found.")

        exercise.type = ExerciseType(command.type)
        exercise.difficulty = Difficulty(command.difficulty)
        exercise.points = command.points
        exercise.content = command.content.strip()
        exercise.answer = command.answer.strip()

        await self._exercise_repo.save(exercise)
        return exercise

    async def deleteExercise(self, exercise_id: UUID) -> None:
        exercise = await self._exercise_repo.get_by_id(exercise_id)
        if exercise is None:
            raise ExerciseNotFoundError(f"Exercise with ID '{exercise_id}' not found.")
        await self._exercise_repo.delete(exercise_id)

    async def getExercise(self, exercise_id: UUID) -> Exercise | None:
        return await self._exercise_repo.get_by_id(exercise_id)

    async def getExercisePublic(self, exercise_id: UUID) -> ExercisePublicDTO | None:
        exercise = await self._exercise_repo.get_by_id(exercise_id)
        return self._to_public_dto(exercise) if exercise else None

    async def getExercisesByLesson(self, lesson_id: UUID) -> list[ExercisePublicDTO]:
        exercises = await self._exercise_repo.list_by_lesson(lesson_id)
        return [self._to_public_dto(e) for e in exercises]

    async def validateAnswer(self, command: ValidateAnswerCommand) -> ValidationResultDTO:
        exercise = await self._exercise_repo.get_by_id(command.exerciseId)
        if exercise is None:
            raise ExerciseNotFoundError(f"Exercise with ID '{command.exerciseId}' not found.")

        is_correct, earned_points = exercise.validate_answer(command.submittedAnswer)
        feedback = (
            "Well done! Sign matched accurately."
            if is_correct
            else f"Sign did not match. Expected: '{exercise.answer}'"
        )

        return ValidationResultDTO(
            isCorrect=is_correct,
            earnedPoints=earned_points,
            expectedAnswer=exercise.answer,
            feedback=feedback,
        )

    @staticmethod
    def _to_public_dto(exercise: Exercise) -> ExercisePublicDTO:
        return ExercisePublicDTO(
            id=exercise.id,
            lessonId=exercise.lessonId,
            type=exercise.type.value,
            difficulty=exercise.difficulty.value,
            points=exercise.points,
            content=exercise.content,
            media=exercise.media,
        )
