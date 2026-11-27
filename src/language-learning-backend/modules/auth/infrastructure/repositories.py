from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.entities import ExternalIdentity, RefreshToken, UserCredentials
from ..domain.repositories import (
    ExternalIdentityRepository,
    RefreshTokenRepository,
    UserCredentialsRepository,
)
from .mappers import AuthMapper
from .models import ExternalIdentityModel, RefreshTokenModel, UserCredentialsModel


class PostgresUserCredentialsRepository(UserCredentialsRepository):
    """
    PostgreSQL / SQLAlchemy implementation of UserCredentialsRepository port.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> UserCredentials | None:
        stmt = select(UserCredentialsModel).where(UserCredentialsModel.id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return AuthMapper.to_credentials_domain(model) if model else None

    async def get_by_email(self, email: str) -> UserCredentials | None:
        normalized_email = email.strip().lower()
        stmt = select(UserCredentialsModel).where(UserCredentialsModel.email == normalized_email)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return AuthMapper.to_credentials_domain(model) if model else None

    async def save(self, credentials: UserCredentials) -> None:
        stmt = select(UserCredentialsModel).where(UserCredentialsModel.id == credentials.id)
        result = await self._session.execute(stmt)
        existing_model = result.scalar_one_or_none()

        if existing_model is None:
            model = AuthMapper.to_credentials_persistence(credentials)
            self._session.add(model)
        else:
            AuthMapper.to_credentials_persistence(credentials, existing=existing_model)

        await self._session.flush()

    async def delete(self, user_id: UUID) -> None:
        stmt = select(UserCredentialsModel).where(UserCredentialsModel.id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()


class PostgresRefreshTokenRepository(RefreshTokenRepository):
    """
    PostgreSQL / SQLAlchemy implementation of RefreshTokenRepository port.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_token(self, token: str) -> RefreshToken | None:
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.token == token)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return AuthMapper.to_refresh_token_domain(model) if model else None

    async def save(self, refresh_token: RefreshToken) -> None:
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.id == refresh_token.id)
        result = await self._session.execute(stmt)
        existing_model = result.scalar_one_or_none()

        if existing_model is None:
            model = AuthMapper.to_refresh_token_persistence(refresh_token)
            self._session.add(model)
        else:
            AuthMapper.to_refresh_token_persistence(refresh_token, existing=existing_model)

        await self._session.flush()

    async def revoke_by_token(self, token: str) -> None:
        stmt = (
            update(RefreshTokenModel)
            .where(RefreshTokenModel.token == token)
            .values(is_revoked=True)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        stmt = (
            update(RefreshTokenModel)
            .where(RefreshTokenModel.user_id == user_id)
            .values(is_revoked=True)
        )
        await self._session.execute(stmt)
        await self._session.flush()


class PostgresExternalIdentityRepository(ExternalIdentityRepository):
    """
    PostgreSQL / SQLAlchemy implementation of ExternalIdentityRepository port.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_provider_and_user_id(
        self, provider: str, provider_user_id: str
    ) -> ExternalIdentity | None:
        stmt = select(ExternalIdentityModel).where(
            ExternalIdentityModel.provider == provider,
            ExternalIdentityModel.provider_user_id == provider_user_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return AuthMapper.to_external_identity_domain(model) if model else None

    async def get_by_system_user_id(self, user_id: UUID) -> list[ExternalIdentity]:
        stmt = select(ExternalIdentityModel).where(ExternalIdentityModel.user_id == user_id)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [AuthMapper.to_external_identity_domain(m) for m in models]

    async def save(self, identity: ExternalIdentity) -> None:
        stmt = select(ExternalIdentityModel).where(ExternalIdentityModel.id == identity.id)
        result = await self._session.execute(stmt)
        existing_model = result.scalar_one_or_none()

        if existing_model is None:
            model = AuthMapper.to_external_identity_persistence(identity)
            self._session.add(model)
        else:
            AuthMapper.to_external_identity_persistence(identity, existing=existing_model)

        await self._session.flush()
