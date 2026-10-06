from dataclasses import dataclass, field
from datetime import date
from uuid import UUID


@dataclass
class DailyActivity:
    """Represents real learning activity performed by a user on a specific calendar day."""

    id: UUID
    userId: UUID
    date: date
    xpEarned: int = 0
    lessonsCompleted: int = 0

    def record_progress(self, xp: int = 0, lessons_completed: int = 0) -> None:
        """Increments XP and completed lessons for the day."""
        if xp > 0:
            self.xpEarned += xp
        if lessons_completed > 0:
            self.lessonsCompleted += lessons_completed


@dataclass
class WeeklyDayActivity:
    """Breakdown for a single day within a weekly report."""

    date: date
    xpEarned: int = 0
    lessonsCompleted: int = 0
    dayOfWeek: str = ""


@dataclass
class WeeklyReport:
    """Weekly report summarizing learning performance across 7 calendar days."""

    userId: UUID
    startDate: date
    endDate: date
    totalXp: int
    lessonsCompleted: int
    activeDaysCount: int
    dailyBreakdown: list[WeeklyDayActivity]
    averageDailyXp: float


@dataclass
class LearningStatistics:
    """Aggregated learning statistics for a learner."""

    userId: UUID
    totalXp: int
    completedLessons: int
    completedCourses: int
    averageAccuracy: float
    activeDaysCount: int
