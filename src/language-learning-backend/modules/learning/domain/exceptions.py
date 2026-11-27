class LearningDomainError(Exception):
    """Base exception for learning domain errors."""
    pass


class UnitNotFoundError(LearningDomainError):
    """Raised when the requested unit does not exist."""
    pass


class LessonNotFoundError(LearningDomainError):
    """Raised when the requested lesson does not exist."""
    pass


class ExerciseNotFoundError(LearningDomainError):
    """Raised when the requested exercise does not exist."""
    pass


class InvalidContentStateError(LearningDomainError):
    """Raised when an invalid state transition is attempted (e.g. publishing an empty or archived unit)."""
    pass


class InvalidOrderError(LearningDomainError):
    """Raised when order sequence is invalid."""
    pass
