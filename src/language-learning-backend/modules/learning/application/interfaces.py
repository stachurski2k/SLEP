from abc import ABC, abstractmethod
from uuid import UUID

from .commands import (
    CreateCourseCommand,
    CreateExerciseCommand,
    CreateLessonCommand,
    CreateUnitCommand,
    UpdateCourseCommand,
    UpdateExerciseCommand,
    UpdateLessonCommand,
    UpdateUnitCommand,
    ValidateAnswerCommand,
)
from .dtos import (
    CourseDetailsDTO,
    CourseDTO,
    ExerciseDTO,
    ExercisePublicDTO,
    LessonDetailsDTO,
    LessonDTO,
    UnitDTO,
    ValidationResultDTO,
)


class CourseApplicationService(ABC):
    """Application service interface for course lifecycle management."""

    @abstractmethod
    async def createCourse(self, command: CreateCourseCommand) -> CourseDTO:
        ...

    @abstractmethod
    async def updateCourse(self, command: UpdateCourseCommand) -> CourseDTO:
        ...

    @abstractmethod
    async def publishCourse(self, course_id: UUID) -> CourseDTO:
        ...

    @abstractmethod
    async def archiveCourse(self, course_id: UUID) -> CourseDTO:
        ...

    @abstractmethod
    async def deleteCourse(self, course_id: UUID) -> None:
        ...

    @abstractmethod
    async def getCourse(self, course_id: UUID) -> CourseDTO | None:
        ...

    @abstractmethod
    async def getCourseDetails(self, course_id: UUID) -> CourseDetailsDTO | None:
        ...

    @abstractmethod
    async def listCourses(
        self,
        language: str | None = None,
        difficulty: str | None = None,
        status: str | None = None,
    ) -> list[CourseDTO]:
        ...


class UnitApplicationService(ABC):
    """Application service interface for course units."""

    @abstractmethod
    async def createUnit(self, command: CreateUnitCommand) -> UnitDTO:
        ...

    @abstractmethod
    async def updateUnit(self, command: UpdateUnitCommand) -> UnitDTO:
        ...

    @abstractmethod
    async def deleteUnit(self, unit_id: UUID) -> None:
        ...

    @abstractmethod
    async def getUnit(self, unit_id: UUID) -> UnitDTO | None:
        ...

    @abstractmethod
    async def getUnitsByCourse(self, course_id: UUID) -> list[UnitDTO]:
        ...


class LessonApplicationService(ABC):
    """Application service interface for unit lessons."""

    @abstractmethod
    async def createLesson(self, command: CreateLessonCommand) -> LessonDTO:
        ...

    @abstractmethod
    async def updateLesson(self, command: UpdateLessonCommand) -> LessonDTO:
        ...

    @abstractmethod
    async def publishLesson(self, lesson_id: UUID) -> LessonDTO:
        ...

    @abstractmethod
    async def deleteLesson(self, lesson_id: UUID) -> None:
        ...

    @abstractmethod
    async def getLesson(self, lesson_id: UUID) -> LessonDTO | None:
        ...

    @abstractmethod
    async def getLessonDetails(self, lesson_id: UUID) -> LessonDetailsDTO | None:
        ...

    @abstractmethod
    async def getLessonsByUnit(self, unit_id: UUID) -> list[LessonDTO]:
        ...


class ExerciseApplicationService(ABC):
    """Application service interface for interactive exercises and validation."""

    @abstractmethod
    async def createExercise(self, command: CreateExerciseCommand) -> ExerciseDTO:
        ...

    @abstractmethod
    async def updateExercise(self, command: UpdateExerciseCommand) -> ExerciseDTO:
        ...

    @abstractmethod
    async def deleteExercise(self, exercise_id: UUID) -> None:
        ...

    @abstractmethod
    async def getExercise(self, exercise_id: UUID) -> ExerciseDTO | None:
        ...

    @abstractmethod
    async def getExercisePublic(self, exercise_id: UUID) -> ExercisePublicDTO | None:
        ...

    @abstractmethod
    async def getExercisesByLesson(self, lesson_id: UUID) -> list[ExercisePublicDTO]:
        ...

    @abstractmethod
    async def validateAnswer(self, command: ValidateAnswerCommand) -> ValidationResultDTO:
        ...
