from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .domain.entities import User
from .domain.repositories import UserRepository
from .domain.value_objects import Email
from .mappers import UserMapper
from .models import UserModel


class PostgresUserRepository(UserRepository):
    """
    SQLAlchemy / PostgreSQL implementation of the UserRepository port.
    Uses UserMapper to convert between persistence models and domain entities.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        stmt = (
            select(UserModel)
            .options(selectinload(UserModel.profile), selectinload(UserModel.preferences))
            .where(UserModel.id == user_id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return UserMapper.to_domain(model) if model else None

    async def get_by_email(self, email: Email | str) -> User | None:
        email_str = str(email.value if isinstance(email, Email) else email).strip().lower()
        stmt = (
            select(UserModel)
            .options(selectinload(UserModel.profile), selectinload(UserModel.preferences))
            .where(UserModel.email == email_str)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return UserMapper.to_domain(model) if model else None

    async def get_by_username(self, username: str) -> User | None:
        stmt = (
            select(UserModel)
            .options(selectinload(UserModel.profile), selectinload(UserModel.preferences))
            .where(UserModel.username == username)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return UserMapper.to_domain(model) if model else None

    async def save(self, user: User) -> None:
        stmt = (
            select(UserModel)
            .options(selectinload(UserModel.profile), selectinload(UserModel.preferences))
            .where(UserModel.id == user.id)
        )
        result = await self._session.execute(stmt)
        existing_model = result.scalar_one_or_none()

        if existing_model is None:
            model = UserMapper.to_persistence(user)
            self._session.add(model)
        else:
            UserMapper.to_persistence(user, existing_model=existing_model)

        await self._session.flush()

    async def delete(self, user: User) -> None:
        stmt = select(UserModel).where(UserModel.id == user.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()
