from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from .exceptions import InvalidOrderError
from .value_objects import ContentStatus, Difficulty, ExerciseType, MediaType


@dataclass
class Media:
    """Instructional media asset (video demo or image reference) attached to an exercise."""
    id: UUID
    exerciseId: UUID
    type: MediaType
    url: str


@dataclass
class Exercise:
    """
    Interactive sign language exercise focusing on practical skill acquisition.
    Contains task prompt (content) and expected sign/sentence answer for instant feedback.
    """
    id: UUID
    lessonId: UUID
    type: ExerciseType
    difficulty: Difficulty
    points: int
    content: str
    answer: str
    media: list[Media] = field(default_factory=list)

    def validate_answer(self, submitted_answer: str) -> tuple[bool, int]:
        """
        Validates user submission against the expected answer with text normalization.
        Returns a tuple: (is_correct, earned_points).
        """
        normalized_expected = " ".join(self.answer.strip().lower().split())
        normalized_submitted = " ".join(submitted_answer.strip().lower().split())

        is_correct = normalized_expected == normalized_submitted
        earned_points = self.points if is_correct else 0
        return is_correct, earned_points


@dataclass
class Lesson:
    """Educational lesson containing interactive exercises."""
    id: UUID
    unitId: UUID
    title: str
    description: str
    order: int
    status: ContentStatus = ContentStatus.DRAFT
    exercises: list[Exercise] = field(default_factory=list)

    def publish(self) -> None:
        """Publishes the lesson, making it accessible to learners."""
        self.status = ContentStatus.PUBLISHED

    def reorder(self, new_order: int) -> None:
        """Updates the sequential order of the lesson within its unit."""
        if new_order < 1:
            raise InvalidOrderError("Lesson order must be at least 1.")
        self.order = new_order


@dataclass
class Unit:
    """Thematic unit grouping a series of related lessons."""
    id: UUID
    title: str
    order: int
    lessons: list[Lesson] = field(default_factory=list)

    def reorder(self, new_order: int) -> None:
        """Updates the sequential order of the unit."""
        if new_order < 1:
            raise InvalidOrderError("Unit order must be at least 1.")
        self.order = new_order
