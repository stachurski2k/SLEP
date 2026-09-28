import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

import bcrypt
import httpx
import jwt

from ..application.ports import OAuthProviderPort, PasswordHasherPort, TokenServicePort
from ..domain.entities import RefreshToken
from ..domain.exceptions import ExternalAuthError, InvalidTokenError, TokenExpiredError

# Security configuration defaults
JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "slep-secret-key-development-minimum-32-chars-long"
)
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


class BcryptPasswordHasher(PasswordHasherPort):
    """
    Password hasher implementation using bcrypt with PBKDF2 backward compatibility.
    """

    def hash(self, password: str) -> str:
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        if not hashed_password:
            return False

        # Support bcrypt
        if hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
            try:
                return bcrypt.checkpw(
                    plain_password.encode("utf-8"),
                    hashed_password.encode("utf-8"),
                )
            except Exception:
                return False

        # Fallback for PBKDF2 (if ever used)
        if hashed_password.startswith("pbkdf2_sha256$"):
            try:
                _, iterations_str, salt, digest = hashed_password.split("$", 3)
                iterations = int(iterations_str)
                derived = hashlib.pbkdf2_hmac(
                    "sha256",
                    plain_password.encode("utf-8"),
                    salt.encode("utf-8"),
                    iterations,
                ).hex()
                return secrets.compare_digest(derived, digest)
            except Exception:
                return False

        return False


class JwtTokenService(TokenServicePort):
    """
    Token service implementation issuing signed JWT access tokens
    and cryptographically secure random refresh tokens.
    """

    def __init__(
        self,
        secret_key: str = JWT_SECRET_KEY,
        algorithm: str = JWT_ALGORITHM,
        access_token_expire_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_token_expire_days: int = RERESH_TOKEN_EXPIRE_DAYS if "RERESH_TOKEN_EXPIRE_DAYS" in locals() else REFRESH_TOKEN_EXPIRE_DAYS,
    ) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_token_expire_minutes = access_token_expire_minutes
        self._refresh_token_expire_days = refresh_token_expire_days

    def create_access_token(self, user_id: UUID, email: str) -> str:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=self._access_token_expire_minutes)

        payload = {
            "sub": str(user_id),
            "email": email,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
        }

        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def create_refresh_token(self, user_id: UUID) -> RefreshToken:
        token_str = secrets.token_urlsafe(64)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=self._refresh_token_expire_days
        )

        return RefreshToken(
            id=uuid4(),
            userId=user_id,
            token=token_str,
            expiresAt=expires_at,
            isRevoked=False,
        )

    def decode_token(self, token: str) -> dict[str, Any]:
        """
        Decodes and verifies a JWT token.
        Raises TokenExpiredError or InvalidTokenError if invalid.
        """
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
            )
            return payload
        except jwt.ExpiredSignatureError as e:
            raise TokenExpiredError("Token has expired.") from e
        except jwt.PyJWTError as e:
            raise InvalidTokenError(f"Invalid token: {e}") from e


class GoogleOAuthProvider(OAuthProviderPort):
    """
    OAuth2 provider adapter for Google Identity Services.
    Validates Google ID tokens via Google TokenInfo API or mock tokens for dev/test.
    """

    GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"

    def __init__(self, google_client_id: str | None = None) -> None:
        self._google_client_id = google_client_id or os.getenv("GOOGLE_CLIENT_ID")

    async def verify_id_token(self, id_token: str) -> dict[str, Any]:
        if not id_token or not id_token.strip():
            raise ExternalAuthError("Google ID token cannot be empty.")

        token = id_token.strip()

        # Development / test mock support
        if token.startswith("mock_") or token.startswith("dev_"):
            clean_sub = token.replace("mock_", "").replace("dev_", "")
            return {
                "provider_user_id": f"google_{clean_sub}",
                "email": f"{clean_sub}@gmail.com" if "@" not in clean_sub else clean_sub,
                "name": f"Mock User {clean_sub}",
            }

        # Live verification against Google tokeninfo endpoint
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.GOOGLE_TOKENINFO_URL,
                    params={"id_token": token},
                )

            if response.status_code != 200:
                raise ExternalAuthError(
                    f"Google token verification failed with status {response.status_code}: {response.text}"
                )

            data = response.json()

            provider_user_id = data.get("sub")
            email = data.get("email")

            if not provider_user_id or not email:
                raise ExternalAuthError("Google ID token did not contain subject or email.")

            # Verify audience if GOOGLE_CLIENT_ID is configured
            if self._google_client_id:
                aud = data.get("aud")
                if aud != self._google_client_id:
                    raise ExternalAuthError(
                        f"Google ID token audience mismatch: expected {self._google_client_id}, got {aud}"
                    )

            return {
                "provider_user_id": provider_user_id,
                "email": email,
                "name": data.get("name"),
                "picture": data.get("picture"),
            }

        except httpx.RequestError as e:
            raise ExternalAuthError(
                f"Network error during Google token verification: {e}"
            ) from e
