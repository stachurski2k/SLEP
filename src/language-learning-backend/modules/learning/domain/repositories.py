from abc import ABC, abstractmethod
from uuid import UUID

from .entities import Exercise, Lesson, Unit


class UnitRepository(ABC):
    """Repository port for Unit entity."""

    @abstractmethod
    async def get_by_id(self, unit_id: UUID) -> Unit | None:
        """Retrieves a unit by its unique identifier."""
        ...

    @abstractmethod
    async def list_all(self) -> list[Unit]:
        """Lists all units ordered by sequence."""
        ...

    @abstractmethod
    async def save(self, unit: Unit) -> None:
        """Persists a new or existing unit."""
        ...

    @abstractmethod
    async def delete(self, unit_id: UUID) -> None:
        """Deletes a unit and its child lessons."""
        ...


class LessonRepository(ABC):
    """Repository port for Lesson entity."""

    @abstractmethod
    async def get_by_id(self, lesson_id: UUID) -> Lesson | None:
        """Retrieves a lesson by its unique identifier."""
        ...

    @abstractmethod
    async def list_by_unit(self, unit_id: UUID) -> list[Lesson]:
        """Lists all lessons belonging to a specific unit ordered by sequence."""
        ...

    @abstractmethod
    async def save(self, lesson: Lesson) -> None:
        """Persists a new or existing lesson."""
        ...

    @abstractmethod
    async def delete(self, lesson_id: UUID) -> None:
        """Deletes a lesson and its exercises."""
        ...


class ExerciseRepository(ABC):
    """Repository port for Exercise entity."""

    @abstractmethod
    async def get_by_id(self, exercise_id: UUID) -> Exercise | None:
        """Retrieves an exercise by its unique identifier (including media)."""
        ...

    @abstractmethod
    async def list_by_lesson(self, lesson_id: UUID) -> list[Exercise]:
        """Lists all exercises belonging to a specific lesson."""
        ...

    @abstractmethod
    async def save(self, exercise: Exercise) -> None:
        """Persists a new or existing exercise."""
        ...

    @abstractmethod
    async def delete(self, exercise_id: UUID) -> None:
        """Deletes an exercise."""
        ...
