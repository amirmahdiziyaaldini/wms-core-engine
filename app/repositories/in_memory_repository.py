from collections.abc import Callable
from typing import Generic, TypeVar

from app.repositories.base_repository import BaseRepository

T = TypeVar("T")


class NotFoundException(Exception):
    pass


class InMemoryRepository(BaseRepository[T], Generic[T]):
    def __init__(self, id_getter: Callable[[T], str]):
        if not callable(id_getter):
            raise ValueError("id_getter must be callable")

        self._id_getter = id_getter
        self._storage: dict[str, T] = {}

    def save(self, entity: T) -> T:
        if entity is None:
            raise ValueError("Entity cannot be None")

        entity_id = self._id_getter(entity)

        if not isinstance(entity_id, str) or not entity_id.strip():
            raise ValueError("Entity ID must be a non-empty string")

        self._storage[entity_id] = entity
        return entity

    def get_by_id(self, entity_id: str) -> T:
        if not isinstance(entity_id, str) or not entity_id.strip():
            raise ValueError("Entity ID must be a non-empty string")

        if entity_id not in self._storage:
            raise NotFoundException(
                f"Entity with id '{entity_id}' was not found"
            )

        return self._storage[entity_id]

    def delete(self, entity_id: str) -> None:
        if not isinstance(entity_id, str) or not entity_id.strip():
            raise ValueError("Entity ID must be a non-empty string")

        if entity_id not in self._storage:
            raise NotFoundException(
                f"Entity with id '{entity_id}' was not found"
            )

        del self._storage[entity_id]

    def list(self) -> list[T]:
        return list(self._storage.values())