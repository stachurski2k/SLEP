from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from .exceptions import InvalidContentStateError, InvalidOrderError
from .value_objects import ContentStatus, Difficulty, ExerciseType, MediaType, SignLanguage


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
    courseId: UUID
    title: str
    order: int
    lessons: list[Lesson] = field(default_factory=list)

    def reorder(self, new_order: int) -> None:
        """Updates the sequential order of the unit within its course."""
        if new_order < 1:
            raise InvalidOrderError("Unit order must be at least 1.")
        self.order = new_order


@dataclass
class Course:
    """Language learning course aggregate root for a specific sign language."""
    id: UUID
    title: str
    description: str
    difficulty: Difficulty
    language: SignLanguage
    status: ContentStatus = ContentStatus.DRAFT
    createdAt: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    units: list[Unit] = field(default_factory=list)

    def publish(self) -> None:
        """Publishes the course to learners."""
        if self.status == ContentStatus.ARCHIVED:
            raise InvalidContentStateError("Cannot publish an archived course directly.")
        self.status = ContentStatus.PUBLISHED

    def archive(self) -> None:
        """Archives the course, removing it from active listings."""
        self.status = ContentStatus.ARCHIVED

    def update_info(
        self,
        title: str,
        description: str,
        difficulty: Difficulty,
        language: SignLanguage,
    ) -> None:
        """Updates main course metadata."""
        self.title = title
        self.description = description
        self.difficulty = difficulty
        self.language = language
