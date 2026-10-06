from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from .entities import DailyActivity


class DailyActivityRepository(ABC):
    """Repository port for DailyActivity entity."""

    @abstractmethod
    async def get_by_user_and_date(
        self, user_id: UUID, activity_date: date
    ) -> DailyActivity | None:
        """Retrieves user activity record for a specific date if activity exists."""
        ...

    @abstractmethod
    async def list_by_user_and_date_range(
        self, user_id: UUID, start_date: date, end_date: date
    ) -> list[DailyActivity]:
        """Lists all existing daily activity records for a user within a date range."""
        ...

    @abstractmethod
    async def count_active_days(self, user_id: UUID) -> int:
        """Counts total number of days with registered user activity."""
        ...

    @abstractmethod
    async def save(self, activity: DailyActivity) -> None:
        """Persists or updates daily activity."""
        ...
