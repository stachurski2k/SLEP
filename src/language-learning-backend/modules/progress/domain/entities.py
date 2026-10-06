from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID


@dataclass
class UserProgress:
    """Global user learning progress and total accumulated XP."""

    id: UUID
    userId: UUID
    xp: int = 0
    createdAt: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_xp(self, amount: int) -> None:
        """Adds experience points to the user's total balance."""
        if amount > 0:
            self.xp += amount
            self.updatedAt = datetime.now(timezone.utc)


@dataclass
class LessonProgress:
    """Progress tracking for a specific lesson attempted by a user."""

    id: UUID
    userId: UUID
    lessonId: UUID
    completed: bool = False
    attempts: int = 0
    completedAt: datetime | None = None
    lastAttemptAt: datetime | None = None

    def start_attempt(self) -> None:
        """Registers a new attempt session for the lesson."""
        self.attempts += 1
        self.lastAttemptAt = datetime.now(timezone.utc)

    def complete(self, xp_reward: int = 10) -> tuple[bool, int]:
        """
        Marks lesson as completed.
        Returns a tuple: (is_first_completion, earned_xp).
        XP is awarded strictly once upon the first successful completion.
        """
        now = datetime.now(timezone.utc)
        self.lastAttemptAt = now

        if not self.completed:
            self.completed = True
            self.completedAt = now
            return True, xp_reward

        return False, 0

    def reset(self) -> None:
        """Resets the lesson progress status."""
        self.completed = False
        self.completedAt = None
        self.attempts = 0
        self.lastAttemptAt = None
