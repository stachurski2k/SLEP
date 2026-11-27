from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class StartLessonCommand:
    """Command to initiate or resume a lesson attempt."""

    userId: UUID
    lessonId: UUID


@dataclass(frozen=True)
class CompleteLessonCommand:
    """Command to complete a lesson and claim completion XP."""

    userId: UUID
    lessonId: UUID
    xpReward: int = 10


@dataclass(frozen=True)
class ResetLessonCommand:
    """Command to reset progress for a given lesson."""

    userId: UUID
    lessonId: UUID
