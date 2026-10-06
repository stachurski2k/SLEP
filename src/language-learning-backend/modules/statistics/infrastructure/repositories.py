from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.entities import DailyActivity
from ..domain.repositories import DailyActivityRepository
from .mappers import StatisticsMapper
from .models import DailyActivityModel


class PostgresDailyActivityRepository(DailyActivityRepository):
    """PostgreSQL implementation of DailyActivityRepository using SQLAlchemy AsyncSession."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_and_date(
        self, user_id: UUID, activity_date: date
    ) -> DailyActivity | None:
        stmt = select(DailyActivityModel).where(
            DailyActivityModel.user_id == user_id,
            DailyActivityModel.activity_date == activity_date,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return StatisticsMapper.to_domain(model) if model else None

    async def list_by_user_and_date_range(
        self, user_id: UUID, start_date: date, end_date: date
    ) -> list[DailyActivity]:
        stmt = (
            select(DailyActivityModel)
            .where(
                DailyActivityModel.user_id == user_id,
                DailyActivityModel.activity_date >= start_date,
                DailyActivityModel.activity_date <= end_date,
            )
            .order_by(DailyActivityModel.activity_date.asc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [StatisticsMapper.to_domain(m) for m in models]

    async def count_active_days(self, user_id: UUID) -> int:
        stmt = (
            select(func.count(DailyActivityModel.id))
            .where(
                DailyActivityModel.user_id == user_id,
                (DailyActivityModel.xp_earned > 0)
                | (DailyActivityModel.lessons_completed > 0),
            )
        )
        result = await self._session.execute(stmt)
        count = result.scalar_one()
        return int(count)

    async def save(self, activity: DailyActivity) -> None:
        stmt = select(DailyActivityModel).where(
            (DailyActivityModel.id == activity.id)
            | (
                (DailyActivityModel.user_id == activity.userId)
                & (DailyActivityModel.activity_date == activity.date)
            )
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            model = StatisticsMapper.to_model(activity)
            self._session.add(model)
        else:
            existing.xp_earned = activity.xpEarned
            existing.lessons_completed = activity.lessonsCompleted

        await self._session.flush()
