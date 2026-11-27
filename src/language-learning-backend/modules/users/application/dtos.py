from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class UserDTO:
    """DTO representing user"""
    id: UUID
    email: str
    username: str
    role: str
    createdAt: datetime
    displayName: str
    country: str | None
    notificationsEnabled: bool
    theme: str
    dailyGoal: int
