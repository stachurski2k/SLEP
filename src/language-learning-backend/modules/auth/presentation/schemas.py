from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


# --- REQUEST SCHEMAS ---

class RegisterRequest(BaseModel):
    """Payload for user registration."""
    email: str = Field(..., description="User email address", examples=["user@example.com"])
    password: str = Field(..., min_length=8, description="Password (at least 8 characters)", examples=["SecurePass123!"])
    passwordConfirmation: str = Field(..., min_length=8, description="Confirmation of password", examples=["SecurePass123!"])


class LoginRequest(BaseModel):
    """Payload for user login with credentials."""
    email: str = Field(..., description="User email address", examples=["user@example.com"])
    password: str = Field(..., description="User password", examples=["SecurePass123!"])


class GoogleLoginRequest(BaseModel):
    """Payload for authentication via Google OAuth2 ID token."""
    idToken: str = Field(..., description="Google OpenID Connect ID token (JWT)", examples=["eyJhbGciOiJSUzI1NiIs..."])


class RefreshTokenRequest(BaseModel):
    """Payload for refreshing an access token."""
    refreshToken: str = Field(..., description="Valid refresh token string")


class LogoutRequest(BaseModel):
    """Payload for logging out a user session."""
    refreshToken: str = Field(..., description="Refresh token to revoke")


class ChangePasswordRequest(BaseModel):
    """Payload for changing the authenticated user's password."""
    currentPassword: str = Field(..., description="Current password")
    newPassword: str = Field(..., min_length=8, description="New password (at least 8 characters)")
    newPasswordConfirmation: str = Field(..., min_length=8, description="Confirmation of new password")


# --- RESPONSE SCHEMAS ---

class TokenResponse(BaseModel):
    """Response representing an access and refresh token pair."""
    model_config = ConfigDict(from_attributes=True)

    accessToken: str
    refreshToken: str
    tokenType: str = "bearer"
    expiresIn: int = 3600


class AuthResponse(BaseModel):
    """Response returned upon successful authentication (register, login, google)."""
    model_config = ConfigDict(from_attributes=True)

    userId: UUID
    email: str
    tokens: TokenResponse


class MessageResponse(BaseModel):
    """Generic status response with message."""
    model_config = ConfigDict(from_attributes=True)

    message: str
