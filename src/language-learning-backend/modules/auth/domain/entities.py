from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from .value_objects import AuthProvider


@dataclass
class UserCredentials:
    """
    Domain entity representing user credentials (email and hashed password).
    """
    id: UUID
    email: str
    passwordHash: str | None
    createdAt: datetime

    def change_password(self, new_password_hash: str) -> None:
        """Updates the hashed password of the user."""
        self.passwordHash = new_password_hash

    @property
    def has_password(self) -> bool:
        """Returns True if the user has a local password set."""
        return bool(self.passwordHash)


@dataclass
class RefreshToken:
    """
    Domain entity representing a Refresh Token.
    """
    id: UUID
    userId: UUID
    token: str
    expiresAt: datetime
    isRevoked: bool = False

    def is_valid(self, now: datetime | None = None) -> bool:
        """Checks if the token is unrevoked and not expired."""
        if self.isRevoked:
            return False
        current_time = now or datetime.now(timezone.utc)
        if self.expiresAt.tzinfo is None:
            expires = self.expiresAt.replace(tzinfo=timezone.utc)
        else:
            expires = self.expiresAt
        return expires > current_time

    def revoke(self) -> None:
        """Revokes the refresh token (e.g. on logout or token rotation)."""
        self.isRevoked = True


@dataclass
class ExternalIdentity:
    """
    Domain entity linking a system user account with an external OAuth provider (e.g. Google).
    """
    id: UUID
    provider: AuthProvider
    providerUserId: str
    userId: UUID