from __future__ import annotations

from uuid import UUID
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

from value_objects import UserRole, Theme


@dataclass
class UserProfile:
    displayName: str
    country: str | None


@dataclass
class Preferences:
    notificationsEnabled: bool
    theme: Theme
    dailyGoal: int


@dataclass
class User:
    """
    User entity aggregator
    """
    id: UUID
    email: str
    username: str
    role: UserRole
    createdAt: datetime
    profile: UserProfile
    preferences: Preferences

