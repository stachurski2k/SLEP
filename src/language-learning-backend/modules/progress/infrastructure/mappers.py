from ..domain.entities import LessonProgress, UserProgress
from .models import LessonProgressModel, UserProgressModel


class ProgressMapper:
    """Bidirectional mapper between domain progress entities and SQLAlchemy models."""

    @staticmethod
    def to_domain_user(model: UserProgressModel) -> UserProgress:
        return UserProgress(
            id=model.id,
            userId=model.user_id,
            xp=model.xp,
            createdAt=model.created_at,
            updatedAt=model.updated_at,
        )

    @staticmethod
    def to_model_user(entity: UserProgress) -> UserProgressModel:
        return UserProgressModel(
            id=entity.id,
            user_id=entity.userId,
            xp=entity.xp,
            created_at=entity.createdAt,
            updated_at=entity.updatedAt,
        )

    @staticmethod
    def to_domain_lesson(model: LessonProgressModel) -> LessonProgress:
        return LessonProgress(
            id=model.id,
            userId=model.user_id,
            lessonId=model.lesson_id,
            completed=model.completed,
            attempts=model.attempts,
            completedAt=model.completed_at,
            lastAttemptAt=model.last_attempt_at,
        )

    @staticmethod
    def to_model_lesson(entity: LessonProgress) -> LessonProgressModel:
        return LessonProgressModel(
            id=entity.id,
            user_id=entity.userId,
            lesson_id=entity.lessonId,
            completed=entity.completed,
            attempts=entity.attempts,
            completed_at=entity.completedAt,
            last_attempt_at=entity.lastAttemptAt,
        )
