from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ...application.commands import CreateCourseCommand, UpdateCourseCommand
from ...application.interfaces import CourseApplicationService
from ...domain.exceptions import CourseNotFoundError, InvalidContentStateError
from ..dependencies import get_course_service
from ..schemas import (
    CourseCreateRequest,
    CourseDetailsResponse,
    CourseResponse,
    CourseUpdateRequest,
)

course_router = APIRouter(prefix="/courses", tags=["Courses"])


@course_router.get("", response_model=list[CourseResponse])
async def list_courses(
    language: str | None = Query(None, description="Filter by sign language: asl or pjm"),
    difficulty: str | None = Query(None, description="Filter by difficulty"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    service: CourseApplicationService = Depends(get_course_service),
) -> list[CourseResponse]:
    courses_dto = await service.listCourses(
        language=language,
        difficulty=difficulty,
        status=status_filter,
    )
    return [CourseResponse.model_validate(c) for c in courses_dto]


@course_router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    schema: CourseCreateRequest,
    service: CourseApplicationService = Depends(get_course_service),
) -> CourseResponse:
    command = CreateCourseCommand(
        title=schema.title,
        description=schema.description,
        difficulty=schema.difficulty.value,
        language=schema.language.value,
    )
    course_dto = await service.createCourse(command)
    return CourseResponse.model_validate(course_dto)


@course_router.get("/{course_id}", response_model=CourseDetailsResponse)
async def get_course_details(
    course_id: UUID,
    service: CourseApplicationService = Depends(get_course_service),
) -> CourseDetailsResponse:
    details_dto = await service.getCourseDetails(course_id)
    if details_dto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID '{course_id}' not found.",
        )
    return CourseDetailsResponse.model_validate(details_dto)


@course_router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: UUID,
    schema: CourseUpdateRequest,
    service: CourseApplicationService = Depends(get_course_service),
) -> CourseResponse:
    command = UpdateCourseCommand(
        courseId=course_id,
        title=schema.title,
        description=schema.description,
        difficulty=schema.difficulty.value,
        language=schema.language.value,
    )
    try:
        course_dto = await service.updateCourse(command)
        return CourseResponse.model_validate(course_dto)
    except CourseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@course_router.post("/{course_id}/publish", response_model=CourseResponse)
async def publish_course(
    course_id: UUID,
    service: CourseApplicationService = Depends(get_course_service),
) -> CourseResponse:
    try:
        course_dto = await service.publishCourse(course_id)
        return CourseResponse.model_validate(course_dto)
    except CourseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidContentStateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@course_router.post("/{course_id}/archive", response_model=CourseResponse)
async def archive_course(
    course_id: UUID,
    service: CourseApplicationService = Depends(get_course_service),
) -> CourseResponse:
    try:
        course_dto = await service.archiveCourse(course_id)
        return CourseResponse.model_validate(course_dto)
    except CourseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@course_router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: UUID,
    service: CourseApplicationService = Depends(get_course_service),
) -> None:
    try:
        await service.deleteCourse(course_id)
    except CourseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
