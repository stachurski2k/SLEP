from uuid import UUID
from abc import ABC, abstractmethod

from .value_objects import Email
from .entities import User

class UserRepository(ABC):
    """
    Repository port for User agregate (domain collection)
    """

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        ...

    @abstractmethod
    async def get_by_email(self, email: Email) -> User | None:
        ...
    
    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        ...

    @abstractmethod
    async def save(self, user: User) -> None:
        ...
    
    @abstractmethod
    async def delete(self, user: User) -> None:
        ...