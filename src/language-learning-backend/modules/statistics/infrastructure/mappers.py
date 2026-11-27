from ..domain.entities import DailyActivity
from .models import DailyActivityModel


class StatisticsMapper:
    """Mapper between domain entities and SQLAlchemy persistence models for statistics."""

    @staticmethod
    def to_domain(model: DailyActivityModel) -> DailyActivity:
        return DailyActivity(
            id=model.id,
            userId=model.user_id,
            date=model.activity_date,
            xpEarned=model.xp_earned,
            lessonsCompleted=model.lessons_completed,
        )

    @staticmethod
    def to_model(entity: DailyActivity) -> DailyActivityModel:
        return DailyActivityModel(
            id=entity.id,
            user_id=entity.userId,
            activity_date=entity.date,
            xp_earned=entity.xpEarned,
            lessons_completed=entity.lessonsCompleted,
        )
