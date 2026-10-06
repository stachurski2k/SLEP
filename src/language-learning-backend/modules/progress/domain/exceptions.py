class ProgressDomainError(Exception):
    """Base exception for progress domain errors."""


class ProgressNotFoundError(ProgressDomainError):
    """Raised when user progress record is not found."""


class LessonProgressNotFoundError(ProgressDomainError):
    """Raised when lesson progress record is not found."""
