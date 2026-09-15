from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from ..domain.entities import RefreshToken


class PasswordHasherPort(ABC):
    """Port for password hashing and verification mechanisms."""

    @abstractmethod
    def hash(self, password: str) -> str:
        """Returns a hashed representation of the password."""
        ...

    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Verifies that the plain password matches the given hash."""
        ...


class TokenServicePort(ABC):
    """Port for generating and verifying authentication tokens (JWT)."""

    @abstractmethod
    def create_access_token(self, user_id: UUID, email: str) -> str:
        """Generates an access token."""
        ...

    @abstractmethod
    def create_refresh_token(self, user_id: UUID) -> RefreshToken:
        """Generates a refresh token entity."""
        ...


class OAuthProviderPort(ABC):
    """Port for external OAuth2 identity providers (e.g. Google)."""

    @abstractmethod
    async def verify_id_token(self, id_token: str) -> dict[str, Any]:
        """
        Verifies an identity token with the OAuth2 provider.
        Returns a dictionary containing at least 'provider_user_id' and 'email'.
        """
        ...
