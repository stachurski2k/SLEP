from uuid import UUID
from abc import ABC,abstractmethod


from .dtos import UserDTO
from .commands import (
    CreateUserCommand,
    DeleteUserCommand,
    UpdateProfileCommand,
    UpdatePreferencesCommand
)


class UserApplicationService(ABC):
    """
    User service containing abstract use cases for user 
    """

    @abstractmethod
    async def createUser(self, command: CreateUserCommand) -> UserDTO:
        ...

    @abstractmethod
    async def getUser(self, user_id: UUID) -> UserDTO | None:
        ...

    @abstractmethod
    async def getUserByEmail(self, user_email: str) -> UserDTO | None:
        ...

    @abstractmethod
    async def getUserByUsername(self, username: str) -> UserDTO | None:
        ...

    @abstractmethod
    async def deleteUser(self, command: DeleteUserCommand) -> None:
        ...

    @abstractmethod
    async def updateProfile(self, command: UpdateProfileCommand) -> UserDTO:
        ...

    @abstractmethod
    async def updatePreferences(self, command: UpdatePreferencesCommand) -> UserDTO:
        ...