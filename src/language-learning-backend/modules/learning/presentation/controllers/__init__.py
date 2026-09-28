from fastapi import APIRouter

from .course import course_router
from .exercise import exercise_router
from .lesson import lesson_router
from .unit import unit_router

# Combined Learning Router
learning_router = APIRouter()
learning_router.include_router(course_router)
learning_router.include_router(unit_router)
learning_router.include_router(lesson_router)
learning_router.include_router(exercise_router)

__all__ = [
    "learning_router",
    "course_router",
    "unit_router",
    "lesson_router",
    "exercise_router",
]
