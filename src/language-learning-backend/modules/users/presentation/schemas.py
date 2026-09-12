from pydantic import ConfigDict
from datetime import datetime
from uuid import UUID
from .domain.value_objects import Theme
from pydantic import Field
from pydantic import BaseModel



# --- REQUESTS SCHEMAS

class UserCreateRequest(BaseModel):
    email: str = Field(..., description="User email")
    username: str = Field(..., min_length=3, max_length=30)
    displayName: str = Field(...,min_length=2, max_length=30)
    country: str | None = Field(default=None)

class UpdateProfileRequest(BaseModel):
    displayName: str = Field(...)
    country: str = Field(...)

class UpdatePreferencesRequest(BaseModel):
    notificationsEnabled: bool = Field(default=False)
    theme: Theme = Field(...)
    dailyGoal: int = Field(..., ge=0) # dailyGoal >= 0


# --- RESPONSES SCHEMAS


class UserResponse(BaseModel):
    """
    Response send back to user in UserDTO format
    """
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True, extra='forbid')

    id: UUID
    email: str
    username: str
    role: str
    createdAt: datetime
    displayName: str
    country: str | None
    notificationsEnabled: bool
    theme: str
    dailyGoal: int
