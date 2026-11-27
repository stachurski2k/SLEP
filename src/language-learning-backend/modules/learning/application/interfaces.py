from abc import ABC, abstractmethod
from uuid import UUID

from ..domain.entities import Exercise, Lesson, Unit
from .commands import (
    CreateExerciseCommand,
    CreateLessonCommand,
    CreateUnitCommand,
    UpdateExerciseCommand,
    UpdateLessonCommand,
    UpdateUnitCommand,
    ValidateAnswerCommand,
)
from .dtos import (
    ExercisePublicDTO,
    ValidationResultDTO,
)


class UnitApplicationService(ABC):
    """Application service interface for learning units."""

    @abstractmethod
    async def createUnit(self, command: CreateUnitCommand) -> Unit:
        ...

    @abstractmethod
    async def updateUnit(self, command: UpdateUnitCommand) -> Unit:
        ...

    @abstractmethod
    async def deleteUnit(self, unit_id: UUID) -> None:
        ...

    @abstractmethod
    async def getUnit(self, unit_id: UUID) -> Unit | None:
        ...

    @abstractmethod
    async def listUnits(self) -> list[Unit]:
        ...


class LessonApplicationService(ABC):
    """Application service interface for unit lessons."""

    @abstractmethod
    async def createLesson(self, command: CreateLessonCommand) -> Lesson:
        ...

    @abstractmethod
    async def updateLesson(self, command: UpdateLessonCommand) -> Lesson:
        ...

    @abstractmethod
    async def publishLesson(self, lesson_id: UUID) -> Lesson:
        ...

    @abstractmethod
    async def deleteLesson(self, lesson_id: UUID) -> None:
        ...

    @abstractmethod
    async def getLesson(self, lesson_id: UUID) -> Lesson | None:
        ...

    @abstractmethod
    async def getLessonDetails(self, lesson_id: UUID) -> Lesson | None:
        ...

    @abstractmethod
    async def getLessonsByUnit(self, unit_id: UUID) -> list[Lesson]:
        ...


class ExerciseApplicationService(ABC):
    """Application service interface for interactive exercises and validation."""

    @abstractmethod
    async def createExercise(self, command: CreateExerciseCommand) -> Exercise:
        ...

    @abstractmethod
    async def updateExercise(self, command: UpdateExerciseCommand) -> Exercise:
        ...

    @abstractmethod
    async def deleteExercise(self, exercise_id: UUID) -> None:
        ...

    @abstractmethod
    async def getExercise(self, exercise_id: UUID) -> Exercise | None:
        ...

    @abstractmethod
    async def getExercisePublic(self, exercise_id: UUID) -> ExercisePublicDTO | None:
        ...

    @abstractmethod
    async def getExercisesByLesson(self, lesson_id: UUID) -> list[ExercisePublicDTO]:
        ...

    @abstractmethod
    async def getExercisesByLessonFull(self, lesson_id: UUID) -> list[Exercise]:
        ...

    @abstractmethod
    async def validateAnswer(self, command: ValidateAnswerCommand) -> ValidationResultDTO:
        ...
