from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserProgressResponse(BaseModel):
    """Global user learning progress and total accumulated XP."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    userId: UUID
    xp: int
    createdAt: datetime
    updatedAt: datetime


class LessonProgressResponse(BaseModel):
    """Progress status for a specific lesson."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    userId: UUID
    lessonId: UUID
    completed: bool
    attempts: int
    completedAt: Optional[datetime] = None
    lastAttemptAt: Optional[datetime] = None


class LessonCompletionResponse(BaseModel):
    """Response returned upon completing a lesson."""

    model_config = ConfigDict(from_attributes=True)

    lessonId: UUID
    isFirstCompletion: bool
    earnedXp: int
    totalXp: int
    completedAt: datetime


class ProgressSummaryResponse(BaseModel):
    """Aggregated learning progress summary for a user."""

    model_config = ConfigDict(from_attributes=True)

    userId: UUID
    totalXp: int
    completedLessonsCount: int
    completedLessonIds: list[UUID] = Field(default_factory=list)
