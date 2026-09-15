from dataclasses import dataclass
from enum import Enum
import re

from .exceptions import InvalidEmailError, InvalidPasswordError


class AuthProvider(str, Enum):
    """Identity / authentication provider."""
    LOCAL = "local"
    GOOGLE = "google"


@dataclass(frozen=True)
class Email:
    """
    Value Object representing a validated and normalized email address.
    """
    value: str

    _EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidEmailError("Email address must be a string.")

        normalized = self.value.strip().lower()
        if not self._EMAIL_REGEX.match(normalized):
            raise InvalidEmailError(f"Invalid email address format: '{self.value}'")

        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class RawPassword:
    """
    Value Object representing a raw password before hashing.
    Enforces minimum security policy (at least 8 characters).
    """
    value: str

    MIN_LENGTH = 8

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidPasswordError("Password must be a string.")

        if len(self.value) < self.MIN_LENGTH:
            raise InvalidPasswordError(
                f"Password must be at least {self.MIN_LENGTH} characters long."
            )

    def __str__(self) -> str:
        return "********"
