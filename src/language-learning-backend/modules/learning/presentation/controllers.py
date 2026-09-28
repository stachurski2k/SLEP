from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..application.commands import (
    CreateCourseCommand,
    CreateExerciseCommand,
    CreateLessonCommand,
    CreateMediaCommand,
    CreateUnitCommand,
    UpdateCourseCommand,
    UpdateExerciseCommand,
    UpdateLessonCommand,
    UpdateUnitCommand,
    ValidateAnswerCommand,
)
from ..application.interfaces import (
    CourseApplicationService,
    ExerciseApplicationService,
    LessonApplicationService,
    UnitApplicationService,
)
from ..domain.exceptions import (
    CourseNotFoundError,
    ExerciseNotFoundError,
    InvalidContentStateError,
    InvalidOrderError,
    LessonNotFoundError,
    UnitNotFoundError,
)
from .dependencies import (
    get_course_service,
    get_exercise_service,
    get_lesson_service,
    get_unit_service,
)
from .schemas import (
    CourseCreateRequest,
    CourseDetailsResponse,
    CourseResponse,
    CourseUpdateRequest,
    ExerciseCreateRequest,
    ExercisePublicResponse,
    ExerciseResponse,
    ExerciseUpdateRequest,
    LessonCreateRequest,
    LessonDetailsResponse,
    LessonResponse,
    LessonUpdateRequest,
    UnitCreateRequest,
    UnitResponse,
    UnitUpdateRequest,
    ValidateAnswerRequest,
    ValidationResultResponse,
)

course_router = APIRouter(prefix="/courses", tags=["Courses"])
unit_router = APIRouter(prefix="/units", tags=["Units"])
lesson_router = APIRouter(prefix="/lessons", tags=["Lessons"])
exercise_router = APIRouter(prefix="/exercises", tags=["Exercises"])


# ============================================================================
# Course Endpoints
# ============================================================================

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


# ============================================================================
# Unit Endpoints
# ============================================================================

@unit_router.post("/for-course/{course_id}", response_model=UnitResponse, status_code=status.HTTP_201_CREATED)
async def create_unit(
    course_id: UUID,
    schema: UnitCreateRequest,
    service: UnitApplicationService = Depends(get_unit_service),
) -> UnitResponse:
    command = CreateUnitCommand(
        courseId=course_id,
        title=schema.title,
        order=schema.order,
    )
    try:
        unit_dto = await service.createUnit(command)
        return UnitResponse.model_validate(unit_dto)
    except CourseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidOrderError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@unit_router.get("/by-course/{course_id}", response_model=list[UnitResponse])
async def get_units_by_course(
    course_id: UUID,
    service: UnitApplicationService = Depends(get_unit_service),
) -> list[UnitResponse]:
    units_dto = await service.getUnitsByCourse(course_id)
    return [UnitResponse.model_validate(u) for u in units_dto]


@unit_router.get("/{unit_id}", response_model=UnitResponse)
async def get_unit(
    unit_id: UUID,
    service: UnitApplicationService = Depends(get_unit_service),
) -> UnitResponse:
    unit_dto = await service.getUnit(unit_id)
    if unit_dto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unit with ID '{unit_id}' not found.",
        )
    return UnitResponse.model_validate(unit_dto)


@unit_router.put("/{unit_id}", response_model=UnitResponse)
async def update_unit(
    unit_id: UUID,
    schema: UnitUpdateRequest,
    service: UnitApplicationService = Depends(get_unit_service),
) -> UnitResponse:
    command = UpdateUnitCommand(
        unitId=unit_id,
        title=schema.title,
        order=schema.order,
    )
    try:
        unit_dto = await service.updateUnit(command)
        return UnitResponse.model_validate(unit_dto)
    except UnitNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidOrderError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@unit_router.delete("/{unit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_unit(
    unit_id: UUID,
    service: UnitApplicationService = Depends(get_unit_service),
) -> None:
    try:
        await service.deleteUnit(unit_id)
    except UnitNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# Lesson Endpoints
# ============================================================================

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


# ============================================================================
# Exercise & Validation Endpoints
# ============================================================================

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


# Combined Learning Router
learning_router = APIRouter()
learning_router.include_router(course_router)
learning_router.include_router(unit_router)
learning_router.include_router(lesson_router)
learning_router.include_router(exercise_router)
