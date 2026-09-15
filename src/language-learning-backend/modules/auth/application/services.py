from datetime import datetime, timezone
from uuid import UUID, uuid4

from ..domain.entities import ExternalIdentity, UserCredentials
from ..domain.exceptions import (
    ExternalAuthError,
    InvalidCredentialsError,
    InvalidTokenError,
    PasswordMismatchError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from ..domain.repositories import (
    ExternalIdentityRepository,
    RefreshTokenRepository,
    UserCredentialsRepository,
)
from ..domain.value_objects import AuthProvider, Email, RawPassword
from .commands import (
    ChangePasswordCommand,
    LoginCommand,
    LoginWithGoogleCommand,
    LogoutCommand,
    RefreshTokenCommand,
    RegisterCommand,
)
from .dtos import AuthResponseDTO, TokenDTO
from .interfaces import AuthApplicationService
from .ports import OAuthProviderPort, PasswordHasherPort, TokenServicePort


class AuthApplicationServiceImpl(AuthApplicationService):
    """
    Concrete implementation of the Auth Application Service.
    Orchestrates authentication business logic, repositories, and cryptographic/token ports.
    """

    def __init__(
        self,
        credentials_repository: UserCredentialsRepository,
        refresh_token_repository: RefreshTokenRepository,
        external_identity_repository: ExternalIdentityRepository,
        password_hasher: PasswordHasherPort,
        token_service: TokenServicePort,
        oauth_provider: OAuthProviderPort,
    ) -> None:
        self._credentials_repo = credentials_repository
        self._refresh_token_repo = refresh_token_repository
        self._external_identity_repo = external_identity_repository
        self._hasher = password_hasher
        self._token_service = token_service
        self._oauth_provider = oauth_provider

    async def register(self, command: RegisterCommand) -> AuthResponseDTO:
        """
        Registers a new user with email and password confirmation.
        """
        if command.password != command.passwordConfirmation:
            raise PasswordMismatchError("Password and password confirmation do not match.")

        email_vo = Email(command.email)
        pwd_vo = RawPassword(command.password)

        existing = await self._credentials_repo.get_by_email(email_vo.value)
        if existing is not None:
            raise UserAlreadyExistsError(
                f"User with email '{command.email}' already exists."
            )

        password_hash = self._hasher.hash(pwd_vo.value)
        user_id = uuid4()

        credentials = UserCredentials(
            id=user_id,
            email=email_vo.value,
            passwordHash=password_hash,
            createdAt=datetime.now(timezone.utc),
        )
        await self._credentials_repo.save(credentials)

        tokens = await self._generate_token_pair(credentials.id, credentials.email)
        return AuthResponseDTO(
            userId=credentials.id,
            email=credentials.email,
            tokens=tokens,
        )

    async def login(self, command: LoginCommand) -> AuthResponseDTO:
        """
        Authenticates a user using credentials and issues JWT tokens.
        """
        email_vo = Email(command.email)
        credentials = await self._credentials_repo.get_by_email(email_vo.value)

        if credentials is None or not credentials.passwordHash:
            raise InvalidCredentialsError("Invalid email or password.")

        if not self._hasher.verify(command.password, credentials.passwordHash):
            raise InvalidCredentialsError("Invalid email or password.")

        tokens = await self._generate_token_pair(credentials.id, credentials.email)
        return AuthResponseDTO(
            userId=credentials.id,
            email=credentials.email,
            tokens=tokens,
        )

    async def loginWithGoogle(self, command: LoginWithGoogleCommand) -> AuthResponseDTO:
        """
        Authenticates a user using an external OAuth2 provider (Google).
        """
        payload = await self._oauth_provider.verify_id_token(command.idToken)
        provider_user_id = payload.get("provider_user_id")
        email_str = payload.get("email")

        if not provider_user_id or not email_str:
            raise ExternalAuthError("Invalid or incomplete Google ID token.")

        email_vo = Email(email_str)

        # 1. Check if the Google external identity is already linked
        external_identity = (
            await self._external_identity_repo.get_by_provider_and_user_id(
                provider=AuthProvider.GOOGLE.value,
                provider_user_id=provider_user_id,
            )
        )

        if external_identity is not None:
            credentials = await self._credentials_repo.get_by_id(external_identity.userId)
            if credentials is None:
                raise UserNotFoundError("User account linked with Google not found.")
        else:
            # 2. Check if a local account with the same email already exists
            credentials = await self._credentials_repo.get_by_email(email_vo.value)

            if credentials is None:
                # Register a new external user account without local password
                credentials = UserCredentials(
                    id=uuid4(),
                    email=email_vo.value,
                    passwordHash=None,
                    createdAt=datetime.now(timezone.utc),
                )
                await self._credentials_repo.save(credentials)

            # Link external identity to user
            new_identity = ExternalIdentity(
                id=uuid4(),
                provider=AuthProvider.GOOGLE,
                providerUserId=provider_user_id,
                userId=credentials.id,
            )
            await self._external_identity_repo.save(new_identity)

        tokens = await self._generate_token_pair(credentials.id, credentials.email)
        return AuthResponseDTO(
            userId=credentials.id,
            email=credentials.email,
            tokens=tokens,
        )

    async def refreshToken(self, command: RefreshTokenCommand) -> TokenDTO:
        """
        Refreshes an access token using a valid refresh token (with token rotation).
        """
        token_entity = await self._refresh_token_repo.get_by_token(command.refreshToken)
        if token_entity is None or not token_entity.is_valid():
            raise InvalidTokenError(
                "Refresh token is invalid, expired, or has been revoked."
            )

        credentials = await self._credentials_repo.get_by_id(token_entity.userId)
        if credentials is None:
            raise UserNotFoundError("User associated with refresh token not found.")

        # Token rotation: revoke old token and issue a fresh pair
        token_entity.revoke()
        await self._refresh_token_repo.save(token_entity)

        return await self._generate_token_pair(credentials.id, credentials.email)

    async def logout(self, command: LogoutCommand) -> None:
        """
        Invalidates active session / user refresh token(s).
        """
        await self._refresh_token_repo.revoke_by_token(command.refreshToken)
        if command.userId:
            await self._refresh_token_repo.revoke_all_for_user(command.userId)

    async def changePassword(self, command: ChangePasswordCommand) -> None:
        """
        Changes the password for an authenticated user with new password confirmation.
        """
        if command.newPassword != command.newPasswordConfirmation:
            raise PasswordMismatchError("New password and confirmation do not match.")

        credentials = await self._credentials_repo.get_by_id(command.userId)
        if credentials is None:
            raise UserNotFoundError(f"User with ID '{command.userId}' does not exist.")

        if credentials.passwordHash:
            if not self._hasher.verify(command.currentPassword, credentials.passwordHash):
                raise InvalidCredentialsError("Current password is incorrect.")

        new_pwd_vo = RawPassword(command.newPassword)
        new_hash = self._hasher.hash(new_pwd_vo.value)

        credentials.change_password(new_hash)
        await self._credentials_repo.save(credentials)

        # Invalidate all active refresh tokens on password change for security
        await self._refresh_token_repo.revoke_all_for_user(command.userId)

    async def _generate_token_pair(self, user_id: UUID, email: str) -> TokenDTO:
        """Helper method to issue and persist a new access and refresh token pair."""
        access_token = self._token_service.create_access_token(user_id, email)
        refresh_token_entity = self._token_service.create_refresh_token(user_id)
        await self._refresh_token_repo.save(refresh_token_entity)

        return TokenDTO(
            accessToken=access_token,
            refreshToken=refresh_token_entity.token,
            tokenType="bearer",
        )
