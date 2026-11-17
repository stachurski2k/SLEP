import logging
import os
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from ..domain.entities import UserCredentials
from ..domain.value_objects import Email, RawPassword, UserRole
from .repositories import PostgresUserCredentialsRepository
from .security import BcryptPasswordHasher

logger = logging.getLogger("language-learning-backend")

DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@admin.pl")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin")


async def ensure_auth_schema_and_default_admin(
    engine: AsyncEngine, session: AsyncSession
) -> UserCredentials:
    """
    Ensures the role column exists in user_credentials and seeds the default administrator account.
    """
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "ALTER TABLE user_credentials "
                "ADD COLUMN IF NOT EXISTS role VARCHAR(50) NOT NULL DEFAULT 'user'"
            )
        )

    repo = PostgresUserCredentialsRepository(session=session)
    hasher = BcryptPasswordHasher()

    email_vo = Email(DEFAULT_ADMIN_EMAIL)
    pwd_vo = RawPassword(DEFAULT_ADMIN_PASSWORD)

    existing = await repo.get_by_email(email_vo.value)
    if existing is None:
        admin_credentials = UserCredentials(
            id=uuid4(),
            email=email_vo.value,
            passwordHash=hasher.hash(pwd_vo.value),
            createdAt=datetime.now(timezone.utc),
            role=UserRole.ADMIN,
        )
        await repo.save(admin_credentials)
        await session.commit()
        logger.info(f"Default administrator account created: {email_vo.value}")
        return admin_credentials

    if (
        existing.role != UserRole.ADMIN
        or not existing.passwordHash
        or not hasher.verify(DEFAULT_ADMIN_PASSWORD, existing.passwordHash)
    ):
        existing.role = UserRole.ADMIN
        existing.passwordHash = hasher.hash(pwd_vo.value)
        await repo.save(existing)
        await session.commit()
        logger.info(
            f"Default administrator account updated to ADMIN role with configured password: {email_vo.value}"
        )

    return existing
