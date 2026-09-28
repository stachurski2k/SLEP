from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ..application.commands import (
    ChangePasswordCommand,
    LoginCommand,
    LoginWithGoogleCommand,
    LogoutCommand,
    RefreshTokenCommand,
    RegisterCommand,
)
from ..application.interfaces import AuthApplicationService
from ..domain.exceptions import (
    ExternalAuthError,
    InvalidCredentialsError,
    InvalidEmailError,
    InvalidPasswordError,
    InvalidTokenError,
    PasswordMismatchError,
    TokenExpiredError,
    TokenRevokedError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from .dependencies import get_auth_service, get_current_user_id
from .schemas import (
    AuthResponse,
    ChangePasswordRequest,
    GoogleLoginRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Registers a user with email and password confirmation, returning credentials and JWT tokens.",
)
async def register(
    schema: RegisterRequest,
    service: AuthApplicationService = Depends(get_auth_service),
) -> AuthResponse:
    command = RegisterCommand(
        email=schema.email,
        password=schema.password,
        passwordConfirmation=schema.passwordConfirmation,
    )
    try:
        dto = await service.register(command)
        return AuthResponse.model_validate(dto)
    except PasswordMismatchError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except (InvalidEmailError, InvalidPasswordError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@auth_router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Log in user",
    description="Authenticates user using email and password, returning JWT access and refresh tokens.",
)
async def login(
    schema: LoginRequest,
    service: AuthApplicationService = Depends(get_auth_service),
) -> AuthResponse:
    command = LoginCommand(
        email=schema.email,
        password=schema.password,
    )
    try:
        dto = await service.login(command)
        return AuthResponse.model_validate(dto)
    except (InvalidCredentialsError, InvalidEmailError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Niepoprawny adres e-mail lub hasło.",
        )


@auth_router.post(
    "/google",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate with Google OAuth2",
    description="Validates Google ID token, creates or links account, and returns JWT tokens.",
)
async def login_with_google(
    schema: GoogleLoginRequest,
    service: AuthApplicationService = Depends(get_auth_service),
) -> AuthResponse:
    command = LoginWithGoogleCommand(idToken=schema.idToken)
    try:
        dto = await service.loginWithGoogle(command)
        return AuthResponse.model_validate(dto)
    except ExternalAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Błąd uwierzytelniania Google: {e}",
        )
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@auth_router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Issues a fresh access and refresh token pair using an existing unrevoked refresh token (token rotation).",
)
async def refresh_token(
    schema: RefreshTokenRequest,
    service: AuthApplicationService = Depends(get_auth_service),
) -> TokenResponse:
    command = RefreshTokenCommand(refreshToken=schema.refreshToken)
    try:
        dto = await service.refreshToken(command)
        return TokenResponse.model_validate(dto)
    except (InvalidTokenError, TokenExpiredError, TokenRevokedError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@auth_router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Log out user",
    description="Revokes the active refresh token and terminates user session.",
)
async def logout(
    schema: LogoutRequest,
    service: AuthApplicationService = Depends(get_auth_service),
) -> MessageResponse:
    command = LogoutCommand(refreshToken=schema.refreshToken)
    await service.logout(command)
    return MessageResponse(message="Wylogowano pomyślnie.")


@auth_router.post(
    "/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Change password",
    description="Changes password for authenticated user and invalidates all existing sessions.",
)
async def change_password(
    schema: ChangePasswordRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    service: AuthApplicationService = Depends(get_auth_service),
) -> MessageResponse:
    command = ChangePasswordCommand(
        userId=current_user_id,
        currentPassword=schema.currentPassword,
        newPassword=schema.newPassword,
        newPasswordConfirmation=schema.newPasswordConfirmation,
    )
    try:
        await service.changePassword(command)
        return MessageResponse(message="Hasło zostało pomyślnie zmienione.")
    except PasswordMismatchError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except (InvalidPasswordError, InvalidCredentialsError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
