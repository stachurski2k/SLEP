from abc import ABC, abstractmethod
from uuid import UUID

from .entities import Course, Exercise, Lesson, Unit
from .value_objects import ContentStatus, Difficulty, SignLanguage


class CourseRepository(ABC):
    """Repository port for Course aggregate."""

    @abstractmethod
    async def get_by_id(self, course_id: UUID) -> Course | None:
        """Retrieves a course by its unique identifier (optionally with units hierarchy)."""
        ...

    @abstractmethod
    async def list_all(
        self,
        language: SignLanguage | None = None,
        difficulty: Difficulty | None = None,
        status: ContentStatus | None = None,
    ) -> list[Course]:
        """Lists courses matching the given filter criteria."""
        ...

    @abstractmethod
    async def save(self, course: Course) -> None:
        """Persists a new or existing course."""
        ...

    @abstractmethod
    async def delete(self, course_id: UUID) -> None:
        """Deletes a course and all child units/lessons via cascade."""
        ...


class UnitRepository(ABC):
    """Repository port for Unit entity."""

    @abstractmethod
    async def get_by_id(self, unit_id: UUID) -> Unit | None:
        """Retrieves a unit by its unique identifier."""
        ...

    @abstractmethod
    async def list_by_course(self, course_id: UUID) -> list[Unit]:
        """Lists all units belonging to a specific course ordered by sequence."""
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
