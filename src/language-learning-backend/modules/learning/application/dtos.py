from dataclasses import dataclass, field
from uuid import UUID

from ..domain.entities import Media


@dataclass(frozen=True)
class ExercisePublicDTO:
    """Public DTO for learners without the answer field to prevent cheating."""

    id: UUID
    lessonId: UUID
    type: str
    difficulty: str
    points: int
    content: str
    media: list[Media] = field(default_factory=list)


@dataclass(frozen=True)
class ValidationResultDTO:
    """Result returned upon validating an exercise submission."""

    isCorrect: bool
    earnedPoints: int
    expectedAnswer: str
    feedback: str
