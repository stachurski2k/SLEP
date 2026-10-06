from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass(frozen=True)
class RecordActivityCommand:
    """Command to register learning activity for a user on a given day."""

    userId: UUID
    xp: int = 0
    lessonsCompleted: int = 0
    activityDate: date | None = None
