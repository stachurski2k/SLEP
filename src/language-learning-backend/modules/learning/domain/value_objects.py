from enum import Enum


class Difficulty(str, Enum):
    """Course and exercise difficulty level."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class SignLanguage(str, Enum):
    """Supported sign languages."""
    ASL = "asl"
    PJM = "pjm"


class ExerciseType(str, Enum):
    """Interactive exercise type focusing on skills-first learning."""
    SINGLE = "single"
    SENTENCE = "sentence"


class ContentStatus(str, Enum):
    """Publication lifecycle status for courses and lessons."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class MediaType(str, Enum):
    """Type of instructional media attached to an exercise."""
    VIDEO = "video"
    IMAGE = "image"
