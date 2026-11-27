from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


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
