from enum import Enum

class UserRole(str, Enum):
    """
    Enum representing available user roles
    """
    USER = "user"
    ADMIN = "admin"

class Theme(str, Enum):
    LIGHT = "light"
    DARK = "dark"