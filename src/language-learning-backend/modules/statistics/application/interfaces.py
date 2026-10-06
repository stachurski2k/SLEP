from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from ..domain.entities import DailyActivity, LearningStatistics, WeeklyReport
from .commands import RecordActivityCommand


class StatisticsApplicationService(ABC):
    """Application service interface for learning statistics."""

    @abstractmethod
    async def recordActivity(
        self, command: RecordActivityCommand
    ) -> DailyActivity | None:
        """Records or increments user learning activity for a calendar date."""
        ...

    @abstractmethod
    async def getLearningStatistics(self, user_id: UUID) -> LearningStatistics:
        """Generates comprehensive learning statistics for a user."""
        ...

    @abstractmethod
    async def getWeeklyReport(
        self, user_id: UUID, reference_date: date | None = None
    ) -> WeeklyReport:
        """Generates a 7-day weekly learning performance breakdown."""
        ...

    @abstractmethod
    async def calculateAccuracy(self, user_id: UUID) -> float:
        """Calculates user accuracy percentage based on lesson completion and attempt ratio."""
        ...
