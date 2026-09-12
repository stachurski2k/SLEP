from datetime import datetime, timezone
from uuid import UUID, uuid4

from .domain.entities import Preferences, User, UserProfile
from .domain.exceptions import (
    InvalidEmailError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from .domain.repositories import UserRepository
from .domain.value_objects import Email, Theme, UserRole
from .commands import (
    CreateUserCommand,
    DeleteUserCommand,
    UpdatePreferencesCommand,
    UpdateProfileCommand,
)
from .dtos import UserDTO
from .use_cases import UserApplicationService


class UserApplicationServiceImpl(UserApplicationService):
    """
    Concrete implementation of UserApplicationService orchestrating the User aggregate.
    """

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    async def createUser(self, command: CreateUserCommand) -> UserDTO:
        email_vo = Email(command.email)

        existing_by_email = await self._user_repository.get_by_email(email_vo)
        if existing_by_email is not None:
            raise UserAlreadyExistsError(f"User with email '{command.email}' already exists.")

        existing_by_username = await self._user_repository.get_by_username(command.username)
        if existing_by_username is not None:
            raise UserAlreadyExistsError(f"Username '{command.username}' is already taken.")

        user = User(
            id=uuid4(),
            email=email_vo.value,
            username=command.username,
            role=UserRole.USER,
            createdAt=datetime.now(timezone.utc),
            profile=UserProfile(
                displayName=command.displayName,
                country=command.country,
            ),
            preferences=Preferences(
                notificationsEnabled=False,
                theme=Theme.LIGHT,
                dailyGoal=50,
            ),
        )

        await self._user_repository.save(user)

        return self._to_dto(user)

    async def getUser(self, user_id: UUID) -> UserDTO | None:
        user = await self._user_repository.get_by_id(user_id)
        return self._to_dto(user) if user else None

    async def getUserByEmail(self, user_email: str) -> UserDTO | None:
        try:
            email_vo = Email(user_email)
        except InvalidEmailError:
            return None
        user = await self._user_repository.get_by_email(email_vo)
        return self._to_dto(user) if user else None

    async def getUserByUsername(self, username: str) -> UserDTO | None:
        user = await self._user_repository.get_by_username(username)
        return self._to_dto(user) if user else None

    async def updateProfile(self, command: UpdateProfileCommand) -> UserDTO:
        user = await self._user_repository.get_by_id(command.userId)
        if user is None:
            raise UserNotFoundError(f"User with ID '{command.userId}' does not exist.")

        user.profile.displayName = command.displayName
        user.profile.country = command.country

        await self._user_repository.save(user)
        return self._to_dto(user)

    async def updatePreferences(self, command: UpdatePreferencesCommand) -> UserDTO:
        user = await self._user_repository.get_by_id(command.userId)
        if user is None:
            raise UserNotFoundError(f"User with ID '{command.userId}' does not exist.")

        user.preferences.notificationsEnabled = command.notificationsEnabled
        user.preferences.theme = (
            command.theme if isinstance(command.theme, Theme) else Theme(command.theme)
        )
        user.preferences.dailyGoal = command.dailyGoal

        await self._user_repository.save(user)
        return self._to_dto(user)

    async def deleteUser(self, command: DeleteUserCommand) -> None:
        user = await self._user_repository.get_by_id(command.userId)
        if user is None:
            raise UserNotFoundError(f"User with ID '{command.userId}' does not exist.")

        await self._user_repository.delete(user)

    @staticmethod
    def _to_dto(user: User) -> UserDTO:
        theme_str = (
            user.preferences.theme.value
            if hasattr(user.preferences.theme, "value")
            else str(user.preferences.theme)
        )
        role_str = (
            user.role.value
            if hasattr(user.role, "value")
            else str(user.role)
        )
        return UserDTO(
            id=user.id,
            email=user.email,
            username=user.username,
            role=role_str,
            createdAt=user.createdAt,
            displayName=user.profile.displayName,
            country=user.profile.country,
            notificationsEnabled=user.preferences.notificationsEnabled,
            theme=theme_str,
            dailyGoal=user.preferences.dailyGoal,
        )
