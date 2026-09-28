from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ...application.commands import CreateLessonCommand, UpdateLessonCommand
from ...application.interfaces import LessonApplicationService
from ...domain.exceptions import InvalidOrderError, LessonNotFoundError, UnitNotFoundError
from ..dependencies import get_lesson_service
from ..schemas import (
    LessonCreateRequest,
    LessonDetailsResponse,
    LessonResponse,
    LessonUpdateRequest,
)

lesson_router = APIRouter(prefix="/lessons", tags=["Lessons"])


@lesson_router.post("/for-unit/{unit_id}", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    unit_id: UUID,
    schema: LessonCreateRequest,
    service: LessonApplicationService = Depends(get_lesson_service),
) -> LessonResponse:
    command = CreateLessonCommand(
        unitId=unit_id,
        title=schema.title,
        description=schema.description,
        order=schema.order,
    )
    try:
        lesson_dto = await service.createLesson(command)
        return LessonResponse.model_validate(lesson_dto)
    except UnitNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidOrderError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@lesson_router.get("/by-unit/{unit_id}", response_model=list[LessonResponse])
async def get_lessons_by_unit(
    unit_id: UUID,
    service: LessonApplicationService = Depends(get_lesson_service),
) -> list[LessonResponse]:
    lessons_dto = await service.getLessonsByUnit(unit_id)
    return [LessonResponse.model_validate(l) for l in lessons_dto]


@lesson_router.get("/{lesson_id}", response_model=LessonDetailsResponse)
async def get_lesson_details(
    lesson_id: UUID,
    service: LessonApplicationService = Depends(get_lesson_service),
) -> LessonDetailsResponse:
    details_dto = await service.getLessonDetails(lesson_id)
    if details_dto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lesson with ID '{lesson_id}' not found.",
        )
    return LessonDetailsResponse.model_validate(details_dto)


@lesson_router.put("/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    lesson_id: UUID,
    schema: LessonUpdateRequest,
    service: LessonApplicationService = Depends(get_lesson_service),
) -> LessonResponse:
    command = UpdateLessonCommand(
        lessonId=lesson_id,
        title=schema.title,
        description=schema.description,
        order=schema.order,
    )
    try:
        lesson_dto = await service.updateLesson(command)
        return LessonResponse.model_validate(lesson_dto)
    except LessonNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidOrderError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@lesson_router.post("/{lesson_id}/publish", response_model=LessonResponse)
async def publish_lesson(
    lesson_id: UUID,
    service: LessonApplicationService = Depends(get_lesson_service),
) -> LessonResponse:
    try:
        lesson_dto = await service.publishLesson(lesson_id)
        return LessonResponse.model_validate(lesson_dto)
    except LessonNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@lesson_router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson_id: UUID,
    service: LessonApplicationService = Depends(get_lesson_service),
) -> None:
    try:
        await service.deleteLesson(lesson_id)
    except LessonNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
