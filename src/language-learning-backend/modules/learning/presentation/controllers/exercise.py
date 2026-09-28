from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ...application.commands import (
    CreateExerciseCommand,
    CreateMediaCommand,
    UpdateExerciseCommand,
    ValidateAnswerCommand,
)
from ...application.interfaces import ExerciseApplicationService
from ...domain.exceptions import ExerciseNotFoundError, LessonNotFoundError
from ..dependencies import get_exercise_service
from ..schemas import (
    ExerciseCreateRequest,
    ExercisePublicResponse,
    ExerciseResponse,
    ExerciseUpdateRequest,
    ValidateAnswerRequest,
    ValidationResultResponse,
)

exercise_router = APIRouter(prefix="/exercises", tags=["Exercises"])


@exercise_router.post("/for-lesson/{lesson_id}", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    lesson_id: UUID,
    schema: ExerciseCreateRequest,
    service: ExerciseApplicationService = Depends(get_exercise_service),
) -> ExerciseResponse:
    command = CreateExerciseCommand(
        lessonId=lesson_id,
        type=schema.type.value,
        difficulty=schema.difficulty.value,
        points=schema.points,
        content=schema.content,
        answer=schema.answer,
        mediaList=[
            CreateMediaCommand(type=m.type.value, url=m.url) for m in schema.media
        ],
    )
    try:
        exercise_dto = await service.createExercise(command)
        return ExerciseResponse.model_validate(exercise_dto)
    except LessonNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@exercise_router.get("/by-lesson/{lesson_id}", response_model=list[ExercisePublicResponse])
async def get_exercises_by_lesson(
    lesson_id: UUID,
    service: ExerciseApplicationService = Depends(get_exercise_service),
) -> list[ExercisePublicResponse]:
    exercises_dto = await service.getExercisesByLesson(lesson_id)
    return [ExercisePublicResponse.model_validate(e) for e in exercises_dto]


@exercise_router.get("/{exercise_id}", response_model=ExercisePublicResponse)
async def get_exercise_public(
    exercise_id: UUID,
    service: ExerciseApplicationService = Depends(get_exercise_service),
) -> ExercisePublicResponse:
    exercise_dto = await service.getExercisePublic(exercise_id)
    if exercise_dto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exercise with ID '{exercise_id}' not found.",
        )
    return ExercisePublicResponse.model_validate(exercise_dto)


@exercise_router.get("/{exercise_id}/full", response_model=ExerciseResponse)
async def get_exercise_full(
    exercise_id: UUID,
    service: ExerciseApplicationService = Depends(get_exercise_service),
) -> ExerciseResponse:
    exercise_dto = await service.getExercise(exercise_id)
    if exercise_dto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exercise with ID '{exercise_id}' not found.",
        )
    return ExerciseResponse.model_validate(exercise_dto)


@exercise_router.put("/{exercise_id}", response_model=ExerciseResponse)
async def update_exercise(
    exercise_id: UUID,
    schema: ExerciseUpdateRequest,
    service: ExerciseApplicationService = Depends(get_exercise_service),
) -> ExerciseResponse:
    command = UpdateExerciseCommand(
        exerciseId=exercise_id,
        type=schema.type.value,
        difficulty=schema.difficulty.value,
        points=schema.points,
        content=schema.content,
        answer=schema.answer,
    )
    try:
        exercise_dto = await service.updateExercise(command)
        return ExerciseResponse.model_validate(exercise_dto)
    except ExerciseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@exercise_router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exercise(
    exercise_id: UUID,
    service: ExerciseApplicationService = Depends(get_exercise_service),
) -> None:
    try:
        await service.deleteExercise(exercise_id)
    except ExerciseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@exercise_router.post("/{exercise_id}/validate", response_model=ValidationResultResponse)
async def validate_exercise_answer(
    exercise_id: UUID,
    schema: ValidateAnswerRequest,
    service: ExerciseApplicationService = Depends(get_exercise_service),
) -> ValidationResultResponse:
    command = ValidateAnswerCommand(
        exerciseId=exercise_id,
        submittedAnswer=schema.submittedAnswer,
    )
    try:
        result_dto = await service.validateAnswer(command)
        return ValidationResultResponse.model_validate(result_dto)
    except ExerciseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
