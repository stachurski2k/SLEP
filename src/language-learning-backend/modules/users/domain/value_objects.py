import re

from .exceptions import InvalidEmailError
from enum import Enum
from dataclasses import dataclass

class UserRole(str, Enum):
    """
    Enum representing available user roles
    """
    USER = "user"
    ADMIN = "admin"

class Theme(str, Enum):
    LIGHT = "light"
    DARK = "dark"


@dataclass(frozen=True)
class Email:
    """
    Value Object representing email address
    Guarantees correctness and immutability.
    """
    value: str
    
    _EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    
    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidEmailError("Email must be a string.")
        
        normalized_value = self.value.strip().lower()
        
        if not self._EMAIL_REGEX.match(normalized_value):
            raise InvalidEmailError(f"Invalid email address: '{self.value}'")
       
        object.__setattr__(self, "value", normalized_value)
    
    def __str__(self) -> str:
        return self.value
