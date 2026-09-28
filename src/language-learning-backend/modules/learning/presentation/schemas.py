from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..domain.value_objects import (
    Difficulty,
    ExerciseType,
    MediaType,
    SignLanguage,
)


# --- Media Schemas ---

class MediaCreateRequest(BaseModel):
    type: MediaType = Field(..., description="Media type: video or image")
    url: str = Field(..., min_length=5, max_length=500, description="Media asset URL")


class MediaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    exerciseId: UUID
    type: str
    url: str


# --- Exercise Schemas ---

class ExerciseCreateRequest(BaseModel):
    type: ExerciseType = Field(..., description="Exercise type: single or sentence")
    difficulty: Difficulty = Field(..., description="Difficulty level")
    points: int = Field(default=10, ge=1, le=100, description="Reward points")
    content: str = Field(..., min_length=1, description="Prompt or task instruction")
    answer: str = Field(..., min_length=1, description="Expected sign or sentence answer")
    media: list[MediaCreateRequest] = Field(default_factory=list, description="Attached media assets")


class ExerciseUpdateRequest(BaseModel):
    type: ExerciseType = Field(..., description="Exercise type: single or sentence")
    difficulty: Difficulty = Field(..., description="Difficulty level")
    points: int = Field(default=10, ge=1, le=100, description="Reward points")
    content: str = Field(..., min_length=1, description="Prompt or task instruction")
    answer: str = Field(..., min_length=1, description="Expected sign or sentence answer")


class ExercisePublicResponse(BaseModel):
    """Public response for learners with answer hidden."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lessonId: UUID
    type: str
    difficulty: str
    points: int
    content: str
    media: list[MediaResponse] = Field(default_factory=list)


class ExerciseResponse(BaseModel):
    """Full exercise response for administrators/creators including answer."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lessonId: UUID
    type: str
    difficulty: str
    points: int
    content: str
    answer: str
    media: list[MediaResponse] = Field(default_factory=list)


class ValidateAnswerRequest(BaseModel):
    submittedAnswer: str = Field(..., min_length=1, description="Learner's submitted sign text")


class ValidationResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    isCorrect: bool
    earnedPoints: int
    expectedAnswer: str
    feedback: str


# --- Lesson Schemas ---

class LessonCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: str = Field(default="", max_length=2000)
    order: int = Field(default=1, ge=1)


class LessonUpdateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: str = Field(default="", max_length=2000)
    order: int = Field(default=1, ge=1)


class LessonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    unitId: UUID
    title: str
    description: str
    order: int
    status: str


class LessonDetailsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    unitId: UUID
    title: str
    description: str
    order: int
    status: str
    exercises: list[ExercisePublicResponse] = Field(default_factory=list)


# --- Unit Schemas ---

class UnitCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    order: int = Field(default=1, ge=1)


class UnitUpdateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    order: int = Field(default=1, ge=1)


class UnitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    courseId: UUID
    title: str
    order: int


class UnitDetailsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    courseId: UUID
    title: str
    order: int
    lessons: list[LessonResponse] = Field(default_factory=list)


# --- Course Schemas ---

class CourseCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: str = Field(default="", max_length=2000)
    difficulty: Difficulty = Field(...)
    language: SignLanguage = Field(..., description="Sign language: asl or pjm")


class CourseUpdateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: str = Field(default="", max_length=2000)
    difficulty: Difficulty = Field(...)
    language: SignLanguage = Field(..., description="Sign language: asl or pjm")


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    difficulty: str
    language: str
    status: str
    createdAt: datetime


class CourseDetailsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    difficulty: str
    language: str
    status: str
    createdAt: datetime
    units: list[UnitDetailsResponse] = Field(default_factory=list)
