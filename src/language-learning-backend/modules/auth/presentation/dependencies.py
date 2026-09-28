from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db

from ..application.interfaces import AuthApplicationService
from ..application.services import AuthApplicationServiceImpl
from ..domain.exceptions import InvalidTokenError, TokenExpiredError
from ..infrastructure.repositories import (
    PostgresExternalIdentityRepository,
    PostgresRefreshTokenRepository,
    PostgresUserCredentialsRepository,
)
from ..infrastructure.security import (
    BcryptPasswordHasher,
    GoogleOAuthProvider,
    JwtTokenService,
)

# Shared security instances
_password_hasher = BcryptPasswordHasher()
_token_service = JwtTokenService()
_oauth_provider = GoogleOAuthProvider()
_http_bearer = HTTPBearer(auto_error=True)


async def get_token_service() -> JwtTokenService:
    """Dependency provider for JWT token service."""
    return _token_service


async def get_auth_service(
    db: AsyncSession = Depends(get_db),
) -> AuthApplicationService:
    """
    Dependency provider injecting repositories and security adapters into AuthApplicationService.
    Follows Clean Architecture dependency inversion principle.
    """
    credentials_repo = PostgresUserCredentialsRepository(session=db)
    refresh_token_repo = PostgresRefreshTokenRepository(session=db)
    external_identity_repo = PostgresExternalIdentityRepository(session=db)

    return AuthApplicationServiceImpl(
        credentials_repository=credentials_repo,
        refresh_token_repository=refresh_token_repo,
        external_identity_repository=external_identity_repo,
        password_hasher=_password_hasher,
        token_service=_token_service,
        oauth_provider=_oauth_provider,
    )


async def get_current_user_id(
    auth_header: HTTPAuthorizationCredentials = Depends(_http_bearer),
    token_service: JwtTokenService = Depends(get_token_service),
) -> UUID:
    """
    Dependency extracting and validating JWT Bearer access token from request header.
    Returns the authenticated user UUID.
    """
    token = auth_header.credentials
    try:
        payload = token_service.decode_token(token)
        token_type = payload.get("type")
        if token_type and token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type: expected access token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        sub = payload.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload is missing subject.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return UUID(sub)

    except TokenExpiredError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (InvalidTokenError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
