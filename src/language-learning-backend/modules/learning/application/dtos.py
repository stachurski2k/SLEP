from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class MediaDTO:
    id: UUID
    exerciseId: UUID
    type: str
    url: str


@dataclass(frozen=True)
class ExercisePublicDTO:
    """Public DTO for learners without the answer field to prevent cheating."""
    id: UUID
    lessonId: UUID
    type: str
    difficulty: str
    points: int
    content: str
    media: list[MediaDTO] = field(default_factory=list)


@dataclass(frozen=True)
class ExerciseDTO:
    """Full exercise DTO including the correct answer for creators / admins."""
    id: UUID
    lessonId: UUID
    type: str
    difficulty: str
    points: int
    content: str
    answer: str
    media: list[MediaDTO] = field(default_factory=list)


@dataclass(frozen=True)
class LessonDTO:
    id: UUID
    unitId: UUID
    title: str
    description: str
    order: int
    status: str


@dataclass(frozen=True)
class LessonDetailsDTO:
    id: UUID
    unitId: UUID
    title: str
    description: str
    order: int
    status: str
    exercises: list[ExercisePublicDTO] = field(default_factory=list)


@dataclass(frozen=True)
class UnitDTO:
    id: UUID
    courseId: UUID
    title: str
    order: int


@dataclass(frozen=True)
class UnitDetailsDTO:
    id: UUID
    courseId: UUID
    title: str
    order: int
    lessons: list[LessonDTO] = field(default_factory=list)


@dataclass(frozen=True)
class CourseDTO:
    id: UUID
    title: str
    description: str
    difficulty: str
    language: str
    status: str
    createdAt: datetime


@dataclass(frozen=True)
class CourseDetailsDTO:
    id: UUID
    title: str
    description: str
    difficulty: str
    language: str
    status: str
    createdAt: datetime
    units: list[UnitDetailsDTO] = field(default_factory=list)


@dataclass(frozen=True)
class ValidationResultDTO:
    isCorrect: bool
    earnedPoints: int
    expectedAnswer: str
    feedback: str
