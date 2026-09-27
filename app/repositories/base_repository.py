from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    @abstractmethod
    def save(self, entity: T) -> T:
        pass

    @abstractmethod
    def get_by_id(self, entity_id: str) -> T:
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> None:
        pass

    @abstractmethod
    def list(self) -> list[T]:
        pass