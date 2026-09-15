from abc import ABC, abstractmethod
from uuid import UUID

from .entities import ExternalIdentity, RefreshToken, UserCredentials


class UserCredentialsRepository(ABC):
    """
    Repository port for UserCredentials entity.
    """

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> UserCredentials | None:
        """Retrieves user credentials by unique identifier."""
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> UserCredentials | None:
        """Retrieves user credentials by email address."""
        ...

    @abstractmethod
    async def save(self, credentials: UserCredentials) -> None:
        """Saves or updates user credentials."""
        ...

    @abstractmethod
    async def delete(self, user_id: UUID) -> None:
        """Deletes user credentials."""
        ...


class RefreshTokenRepository(ABC):
    """
    Repository port for RefreshToken entity.
    """

    @abstractmethod
    async def get_by_token(self, token: str) -> RefreshToken | None:
        """Finds a refresh token by its raw token string."""
        ...

    @abstractmethod
    async def save(self, refresh_token: RefreshToken) -> None:
        """Persists a new or updated refresh token."""
        ...

    @abstractmethod
    async def revoke_by_token(self, token: str) -> None:
        """Marks the specified refresh token as revoked."""
        ...

    @abstractmethod
    async def revoke_all_for_user(self, user_id: UUID) -> None:
        """Revokes all active refresh tokens for the given user."""
        ...


class ExternalIdentityRepository(ABC):
    """
    Repository port for external OAuth2 identities.
    """

    @abstractmethod
    async def get_by_provider_and_user_id(
        self, provider: str, provider_user_id: str
    ) -> ExternalIdentity | None:
        """Retrieves an external identity by provider and provider user identifier."""
        ...

    @abstractmethod
    async def get_by_system_user_id(self, user_id: UUID) -> list[ExternalIdentity]:
        """Retrieves all external identities linked to a system user."""
        ...

    @abstractmethod
    async def save(self, identity: ExternalIdentity) -> None:
        """Persists an external identity linkage."""
        ...
