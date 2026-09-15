from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class TokenDTO:
    """DTO representing a pair of authentication JWT tokens."""
    accessToken: str
    refreshToken: str
    tokenType: str = "bearer"
    expiresIn: int = 3600  # Access token lifetime in seconds


@dataclass(frozen=True)
class AuthResponseDTO:
    """DTO returned upon successful authentication (registration, login)."""
    userId: UUID
    email: str
    tokens: TokenDTO


@dataclass(frozen=True)
class UserCredentialsDTO:
    """DTO representing basic user authentication data."""
    id: UUID
    email: str
    hasPassword: bool
    createdAt: datetime
