from uuid import UUID
from dataclasses import dataclass

@dataclass(frozen=True)
class CreateUserCommand:
    email: str
    username: str
    displayName: str
    country: str | None = None # default None

@dataclass(frozen=True)
class UpdateProfileCommand:
    userId: UUID
    displayName: str
    country: str | None

@dataclass(frozen=True)
class UpdatePreferencesCommand:
    userId: UUID
    notificationsEnabled: bool
    theme: str
    dailyGoal: int
    
@dataclass(frozen=True)
class DeleteUserCommand:
    userId: UUID