from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RegisterCommand:
    """Command to register a new user with email and password confirmation."""
    email: str
    password: str
    passwordConfirmation: str


@dataclass(frozen=True)
class LoginCommand:
    """Command to authenticate a user using credentials."""
    email: str
    password: str


@dataclass(frozen=True)
class LoginWithGoogleCommand:
    """Command to authenticate a user using a Google OAuth2 ID token."""
    idToken: str


@dataclass(frozen=True)
class RefreshTokenCommand:
    """Command to refresh an access token using a refresh token."""
    refreshToken: str


@dataclass(frozen=True)
class LogoutCommand:
    """Command to log out a user and invalidate token(s)."""
    refreshToken: str
    userId: UUID | None = None


@dataclass(frozen=True)
class ChangePasswordCommand:
    """Command to change the password for an authenticated user."""
    userId: UUID
    currentPassword: str
    newPassword: str
    newPasswordConfirmation: str
