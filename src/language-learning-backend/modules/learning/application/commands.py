from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class CreateCourseCommand:
    title: str
    description: str
    difficulty: str
    language: str


@dataclass(frozen=True)
class UpdateCourseCommand:
    courseId: UUID
    title: str
    description: str
    difficulty: str
    language: str


@dataclass(frozen=True)
class CreateUnitCommand:
    courseId: UUID
    title: str
    order: int


@dataclass(frozen=True)
class UpdateUnitCommand:
    unitId: UUID
    title: str
    order: int


@dataclass(frozen=True)
class CreateLessonCommand:
    unitId: UUID
    title: str
    description: str
    order: int


@dataclass(frozen=True)
class UpdateLessonCommand:
    lessonId: UUID
    title: str
    description: str
    order: int


@dataclass(frozen=True)
class CreateMediaCommand:
    type: str
    url: str


@dataclass(frozen=True)
class CreateExerciseCommand:
    lessonId: UUID
    type: str
    difficulty: str
    points: int
    content: str
    answer: str
    mediaList: list[CreateMediaCommand] = field(default_factory=list)


@dataclass(frozen=True)
class UpdateExerciseCommand:
    exerciseId: UUID
    type: str
    difficulty: str
    points: int
    content: str
    answer: str


@dataclass(frozen=True)
class ValidateAnswerCommand:
    exerciseId: UUID
    submittedAnswer: str
