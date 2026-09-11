from uuid import UUID
from fastapi import APIRouter, Depends, status

from ..application.use_cases import UserApplicationService
from .schemas import (
    UpdatePreferencesRequest,
    UpdateProfileRequest,
    UserCreateRequest,
    UserResponse,
)

user_router = APIRouter(prefix="/user", tags=["User"])


@user_router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: UUID, service: UserApplicationService = Depends()):
    ...


@user_router.get("/email/{email}", response_model=UserResponse)
async def get_user_by_email(email: str, service: UserApplicationService = Depends()):
    ...


@user_router.get("/username/{username}", response_model=UserResponse)
async def get_user_by_username(username: str, service: UserApplicationService = Depends()):
    ...


@user_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: UUID, service: UserApplicationService = Depends()):
    ...


@user_router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(schema: UserCreateRequest, service: UserApplicationService = Depends()):
    ...


@user_router.put("/profile/{user_id}", response_model=UserResponse)
async def update_user_profile(
    user_id: UUID,
    schema: UpdateProfileRequest,
    service: UserApplicationService = Depends(),
):
    ...


@user_router.put("/preferences/{user_id}", response_model=UserResponse)
async def update_user_preferences(
    user_id: UUID,
    schema: UpdatePreferencesRequest,
    service: UserApplicationService = Depends(),
):
    ...
