from uuid import UUID

from fastapi import APIRouter, Depends, status

from modules.auth.presentation.dependencies import get_current_user_id

from ...application.commands import (
    CompleteLessonCommand,
    ResetLessonCommand,
    StartLessonCommand,
)
from ...application.interfaces import ProgressApplicationService
from ..dependencies import get_progress_service
from ..schemas import (
    LessonCompletionResponse,
    LessonProgressResponse,
    ProgressSummaryResponse,
    UserProgressResponse,
)

progress_router = APIRouter(prefix="/progress", tags=["Progress"])


@progress_router.get("/summary", response_model=ProgressSummaryResponse)
async def get_progress_summary(
    current_user_id: UUID = Depends(get_current_user_id),
    service: ProgressApplicationService = Depends(get_progress_service),
) -> ProgressSummaryResponse:
    """Retrieves aggregated user learning summary (total XP and completed lessons)."""
    summary_dto = await service.getProgressSummary(current_user_id)
    return ProgressSummaryResponse.model_validate(summary_dto)


@progress_router.get("", response_model=UserProgressResponse)
async def get_user_progress(
    current_user_id: UUID = Depends(get_current_user_id),
    service: ProgressApplicationService = Depends(get_progress_service),
) -> UserProgressResponse:
    """Retrieves global user learning progress record."""
    progress_dto = await service.getUserProgress(current_user_id)
    return UserProgressResponse.model_validate(progress_dto)


@progress_router.get("/lessons/{lesson_id}", response_model=LessonProgressResponse)
async def get_lesson_progress(
    lesson_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: ProgressApplicationService = Depends(get_progress_service),
) -> LessonProgressResponse:
    """Retrieves progress record for a specific lesson."""
    lesson_dto = await service.getLessonProgress(current_user_id, lesson_id)
    return LessonProgressResponse.model_validate(lesson_dto)


@progress_router.post("/lessons/{lesson_id}/start", response_model=LessonProgressResponse)
async def start_lesson(
    lesson_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: ProgressApplicationService = Depends(get_progress_service),
) -> LessonProgressResponse:
    """Registers the start of a lesson attempt session."""
    command = StartLessonCommand(userId=current_user_id, lessonId=lesson_id)
    lesson_dto = await service.startLesson(command)
    return LessonProgressResponse.model_validate(lesson_dto)


@progress_router.post("/lessons/{lesson_id}/complete", response_model=LessonCompletionResponse)
async def complete_lesson(
    lesson_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: ProgressApplicationService = Depends(get_progress_service),
) -> LessonCompletionResponse:
    """
    Completes a lesson.
    Awards 10 XP on the first completion and updates global user XP.
    Subsequent completions do not award extra XP.
    """
    command = CompleteLessonCommand(userId=current_user_id, lessonId=lesson_id, xpReward=10)
    result_dto = await service.completeLesson(command)
    return LessonCompletionResponse.model_validate(result_dto)


@progress_router.post("/lessons/{lesson_id}/reset", response_model=LessonProgressResponse)
async def reset_lesson(
    lesson_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: ProgressApplicationService = Depends(get_progress_service),
) -> LessonProgressResponse:
    """Resets progress and attempt counters for a specific lesson."""
    command = ResetLessonCommand(userId=current_user_id, lessonId=lesson_id)
    lesson_dto = await service.resetLesson(command)
    return LessonProgressResponse.model_validate(lesson_dto)
