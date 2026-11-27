from abc import ABC, abstractmethod

from .commands import (
    ChangePasswordCommand,
    LoginCommand,
    LoginWithGoogleCommand,
    LogoutCommand,
    RefreshTokenCommand,
    RegisterCommand,
)
from .dtos import AuthResponseDTO, TokenDTO


class AuthApplicationService(ABC):
    """
    Abstract interface for authentication application services.
    Conforms to the Authentication Bounded Context specification.
    """

    @abstractmethod
    async def register(self, command: RegisterCommand) -> AuthResponseDTO:
        """Registers a new user with email and password."""
        ...

    @abstractmethod
    async def login(self, command: LoginCommand) -> AuthResponseDTO:
        """Authenticates a user using credentials and issues JWT tokens."""
        ...

    @abstractmethod
    async def loginWithGoogle(self, command: LoginWithGoogleCommand) -> AuthResponseDTO:
        """Authenticates a user using external OAuth2 provider (Google)."""
        ...

    @abstractmethod
    async def refreshToken(self, command: RefreshTokenCommand) -> TokenDTO:
        """Refreshes an access token using a valid refresh token."""
        ...

    @abstractmethod
    async def logout(self, command: LogoutCommand) -> None:
        """Invalidates active session / user refresh token."""
        ...

    @abstractmethod
    async def changePassword(self, command: ChangePasswordCommand) -> None:
        """Changes the password for an authenticated user."""
        ...
