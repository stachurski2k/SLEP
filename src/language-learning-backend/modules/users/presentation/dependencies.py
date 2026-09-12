from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db

from .application.services import UserApplicationServiceImpl
from .application.interfaces import UserApplicationService
from .infrastructure.postgres_user_repository import PostgresUserRepository


async def get_user_service(
    db: AsyncSession = Depends(get_db),
) -> UserApplicationService:
    """Dependency provider injecting repository into application service."""
    repository = PostgresUserRepository(session=db)
    return UserApplicationServiceImpl(user_repository=repository)