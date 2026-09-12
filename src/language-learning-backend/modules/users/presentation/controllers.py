from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from .application.commands import (
    CreateUserCommand,
    DeleteUserCommand,
    UpdatePreferencesCommand,
    UpdateProfileCommand,
)
from .application.interfaces import UserApplicationService
from .domain.exceptions import (
    InvalidEmailError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from .dependencies import get_user_service
from .schemas import (
    UpdatePreferencesRequest,
    UpdateProfileRequest,
    UserCreateRequest,
    UserResponse,
)

user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    schema: UserCreateRequest,
    service: UserApplicationService = Depends(get_user_service),
) -> UserResponse:
    command = CreateUserCommand(
        email=schema.email,
        username=schema.username,
        displayName=schema.displayName,
        country=schema.country,
    )
    try:
        user_dto = await service.createUser(command)
        return UserResponse.model_validate(user_dto)
    except InvalidEmailError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@user_router.get(
    "/{user_id}",
    response_model=UserResponse,
)
async def get_user_by_id(
    user_id: UUID,
    service: UserApplicationService = Depends(get_user_service),
) -> UserResponse:
    user_dto = await service.getUser(user_id)
    if user_dto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Użytkownik o ID {user_id} nie istnieje.",
        )
    return UserResponse.model_validate(user_dto)


@user_router.get(
    "/email/{email}",
    response_model=UserResponse,
)
async def get_user_by_email(
    email: str,
    service: UserApplicationService = Depends(get_user_service),
) -> UserResponse:
    user_dto = await service.getUserByEmail(email)
    if user_dto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Użytkownik z adresem e-mail '{email}' nie istnieje.",
        )
    return UserResponse.model_validate(user_dto)


@user_router.get(
    "/username/{username}",
    response_model=UserResponse,
)
async def get_user_by_username(
    username: str,
    service: UserApplicationService = Depends(get_user_service),
) -> UserResponse:
    user_dto = await service.getUserByUsername(username)
    if user_dto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Użytkownik o nazwie '{username}' nie istnieje.",
        )
    return UserResponse.model_validate(user_dto)


@user_router.put(
    "/{user_id}/profile",
    response_model=UserResponse,
)
async def update_user_profile(
    user_id: UUID,
    schema: UpdateProfileRequest,
    service: UserApplicationService = Depends(get_user_service),
) -> UserResponse:
    command = UpdateProfileCommand(
        userId=user_id,
        displayName=schema.displayName,
        country=schema.country,
    )
    try:
        user_dto = await service.updateProfile(command)
        return UserResponse.model_validate(user_dto)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Użytkownik o ID {user_id} nie istnieje.",
        )


@user_router.put(
    "/{user_id}/preferences",
    response_model=UserResponse,
)
async def update_user_preferences(
    user_id: UUID,
    schema: UpdatePreferencesRequest,
    service: UserApplicationService = Depends(get_user_service),
) -> UserResponse:
    theme_val = (
        schema.theme.value if hasattr(schema.theme, "value") else str(schema.theme)
    )
    command = UpdatePreferencesCommand(
        userId=user_id,
        notificationsEnabled=schema.notificationsEnabled,
        theme=theme_val,
        dailyGoal=schema.dailyGoal,
    )
    try:
        user_dto = await service.updatePreferences(command)
        return UserResponse.model_validate(user_dto)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Użytkownik o ID {user_id} nie istnieje.",
        )


@user_router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    user_id: UUID,
    service: UserApplicationService = Depends(get_user_service),
) -> None:
    command = DeleteUserCommand(userId=user_id)
    try:
        await service.deleteUser(command)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Użytkownik o ID {user_id} nie istnieje.",
        )
