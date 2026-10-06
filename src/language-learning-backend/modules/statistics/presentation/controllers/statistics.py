from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from modules.auth.presentation.dependencies import get_current_user_id

from ...application.commands import RecordActivityCommand
from ...application.interfaces import StatisticsApplicationService
from ..dependencies import get_statistics_service
from ..schemas import (
    AccuracyResponse,
    DailyActivityResponse,
    LearningStatisticsResponse,
    RecordActivityRequest,
    WeeklyReportResponse,
)

statistics_router = APIRouter(prefix="/statistics", tags=["Statistics"])


@statistics_router.get("", response_model=LearningStatisticsResponse)
async def get_learning_statistics(
    current_user_id: UUID = Depends(get_current_user_id),
    service: StatisticsApplicationService = Depends(get_statistics_service),
) -> LearningStatisticsResponse:
    """Retrieves aggregated learning statistics for the current authenticated user."""
    stats = await service.getLearningStatistics(current_user_id)
    return LearningStatisticsResponse.model_validate(stats)


@statistics_router.get("/weekly", response_model=WeeklyReportResponse)
async def get_weekly_report(
    reference_date: date | None = Query(
        None,
        alias="date",
        description="Reference calendar date within the target week (defaults to today)",
    ),
    current_user_id: UUID = Depends(get_current_user_id),
    service: StatisticsApplicationService = Depends(get_statistics_service),
) -> WeeklyReportResponse:
    """Generates a 7-day weekly learning performance breakdown for the authenticated user."""
    report = await service.getWeeklyReport(current_user_id, reference_date=reference_date)
    return WeeklyReportResponse.model_validate(report)


@statistics_router.get("/accuracy", response_model=AccuracyResponse)
async def get_accuracy(
    current_user_id: UUID = Depends(get_current_user_id),
    service: StatisticsApplicationService = Depends(get_statistics_service),
) -> AccuracyResponse:
    """Retrieves user accuracy percentage based on completed lessons and attempts."""
    accuracy = await service.calculateAccuracy(current_user_id)
    return AccuracyResponse(accuracy=accuracy)


@statistics_router.post("/record", response_model=DailyActivityResponse | None)
async def record_activity(
    schema: RecordActivityRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    service: StatisticsApplicationService = Depends(get_statistics_service),
) -> DailyActivityResponse | None:
    """Records learning activity for a day if non-zero progress was made."""
    command = RecordActivityCommand(
        userId=current_user_id,
        xp=schema.xp,
        lessonsCompleted=schema.lessonsCompleted,
        activityDate=schema.activityDate,
    )
    result = await service.recordActivity(command)
    return DailyActivityResponse.model_validate(result) if result else None
