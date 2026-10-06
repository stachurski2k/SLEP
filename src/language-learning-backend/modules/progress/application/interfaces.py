from abc import ABC, abstractmethod
from uuid import UUID

from .commands import CompleteLessonCommand, ResetLessonCommand, StartLessonCommand
from .dtos import (
    LessonCompletionResultDTO,
    LessonProgressDTO,
    ProgressSummaryDTO,
    UserProgressDTO,
)


class ProgressApplicationService(ABC):
    """Application service interface for progress management."""

    @abstractmethod
    async def getUserProgress(self, user_id: UUID) -> UserProgressDTO:
        """Retrieves or initializes the global user progress record."""
        ...

    @abstractmethod
    async def getProgressSummary(self, user_id: UUID) -> ProgressSummaryDTO:
        """Retrieves aggregated user progress including total XP and completed lessons."""
        ...

    @abstractmethod
    async def getLessonProgress(
        self, user_id: UUID, lesson_id: UUID
    ) -> LessonProgressDTO:
        """Retrieves user progress for a specific lesson."""
        ...

    @abstractmethod
    async def startLesson(self, command: StartLessonCommand) -> LessonProgressDTO:
        """Registers a start/attempt for a lesson."""
        ...

    @abstractmethod
    async def completeLesson(
        self, command: CompleteLessonCommand
    ) -> LessonCompletionResultDTO:
        """Marks a lesson as completed, granting XP strictly once."""
        ...

    @abstractmethod
    async def resetLesson(self, command: ResetLessonCommand) -> LessonProgressDTO:
        """Resets the progress for a specific lesson."""
        ...
