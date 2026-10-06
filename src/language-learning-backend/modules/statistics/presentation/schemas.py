from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DailyActivityResponse(BaseModel):
    """Response schema for a single daily activity entry."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    userId: UUID
    date: date
    xpEarned: int
    lessonsCompleted: int


class WeeklyDayActivityResponse(BaseModel):
    """Response schema for a single day breakdown in the weekly report."""

    model_config = ConfigDict(from_attributes=True)

    date: date
    xpEarned: int
    lessonsCompleted: int
    dayOfWeek: str


class WeeklyReportResponse(BaseModel):
    """Response schema for the 7-day weekly learning performance breakdown."""

    model_config = ConfigDict(from_attributes=True)

    userId: UUID
    startDate: date
    endDate: date
    totalXp: int
    lessonsCompleted: int
    activeDaysCount: int
    dailyBreakdown: list[WeeklyDayActivityResponse]
    averageDailyXp: float


class LearningStatisticsResponse(BaseModel):
    """Response schema for aggregated user learning statistics."""

    model_config = ConfigDict(from_attributes=True)

    userId: UUID
    totalXp: int
    completedLessons: int
    completedCourses: int
    averageAccuracy: float
    activeDaysCount: int


class AccuracyResponse(BaseModel):
    """Response schema for user accuracy percentage."""

    accuracy: float


class RecordActivityRequest(BaseModel):
    """Request payload to manually register learning activity."""

    xp: int = Field(default=0, ge=0, description="XP gained")
    lessonsCompleted: int = Field(default=0, ge=0, description="Lessons completed")
    activityDate: Optional[date] = Field(default=None, description="Optional custom date (defaults to today)")
