from abc import ABC, abstractmethod
from uuid import UUID

from .entities import LessonProgress, UserProgress


class UserProgressRepository(ABC):
    """Repository port for UserProgress aggregate."""

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> UserProgress | None:
        """Retrieves global user progress by user ID."""
        ...

    @abstractmethod
    async def save(self, user_progress: UserProgress) -> None:
        """Persists or updates user progress."""
        ...


class LessonProgressRepository(ABC):
    """Repository port for LessonProgress entity."""

    @abstractmethod
    async def get_by_user_and_lesson(
        self, user_id: UUID, lesson_id: UUID
    ) -> LessonProgress | None:
        """Retrieves lesson progress for a specific user and lesson."""
        ...

    @abstractmethod
    async def list_by_user_id(self, user_id: UUID) -> list[LessonProgress]:
        """Lists all lesson progress records for a user."""
        ...

    @abstractmethod
    async def list_completed_by_user_id(self, user_id: UUID) -> list[LessonProgress]:
        """Lists only completed lesson progress records for a user."""
        ...

    @abstractmethod
    async def save(self, lesson_progress: LessonProgress) -> None:
        """Persists or updates lesson progress."""
        ...

    @abstractmethod
    async def delete(self, user_id: UUID, lesson_id: UUID) -> None:
        """Deletes lesson progress for a specific user and lesson."""
        ...
