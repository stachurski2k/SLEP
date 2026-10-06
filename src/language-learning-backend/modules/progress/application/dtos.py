from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class UserProgressDTO:
    """Data transfer object for global user learning progress."""

    id: UUID
    userId: UUID
    xp: int
    createdAt: datetime
    updatedAt: datetime


@dataclass(frozen=True)
class LessonProgressDTO:
    """Data transfer object for individual lesson progress."""

    id: UUID
    userId: UUID
    lessonId: UUID
    completed: bool
    attempts: int
    completedAt: datetime | None
    lastAttemptAt: datetime | None


@dataclass(frozen=True)
class LessonCompletionResultDTO:
    """Result returned upon completing a lesson."""

    lessonId: UUID
    isFirstCompletion: bool
    earnedXp: int
    totalXp: int
    completedAt: datetime


@dataclass(frozen=True)
class ProgressSummaryDTO:
    """Aggregated learning progress summary for a user."""

    userId: UUID
    totalXp: int
    completedLessonsCount: int
    completedLessonIds: list[UUID]
