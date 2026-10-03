from typing import Generic, TypeVar

from app.domain.exceptions.entity_not_found import EntityNotFoundError


T = TypeVar("T")


class InMemoryRepository(Generic[T]):
    def __init__(self):
        self._storage: dict[str, T] = {}

    def save(
        self,
        entity_id: str,
        entity: T,
    ) -> T:
        if not isinstance(entity_id, str):
            raise ValueError(
                "Entity ID must be a string"
            )

        if not entity_id.strip():
            raise ValueError(
                "Entity ID cannot be empty"
            )

        if entity is None:
            raise ValueError(
                "Entity cannot be None"
            )

        if entity_id in self._storage:
            raise ValueError(
                f"Entity already exists: {entity_id}"
            )

        self._storage[entity_id] = entity

        return entity

    def get(
        self,
        entity_id: str,
    ) -> T:
        if not isinstance(entity_id, str):
            raise ValueError(
                "Entity ID must be a string"
            )

        if not entity_id.strip():
            raise ValueError(
                "Entity ID cannot be empty"
            )

        if entity_id not in self._storage:
            raise EntityNotFoundError(
                self.__class__.__name__,
                entity_id,
            )

        return self._storage[entity_id]

    def list(self) -> list[T]:
        return list(self._storage.values())

    def delete(
        self,
        entity_id: str,
    ) -> None:
        if not isinstance(entity_id, str):
            raise ValueError(
                "Entity ID must be a string"
            )

        if not entity_id.strip():
            raise ValueError(
                "Entity ID cannot be empty"
            )

        if entity_id not in self._storage:
            raise EntityNotFoundError(
                self.__class__.__name__,
                entity_id,
            )

        del self._storage[entity_id]

    def exists(
        self,
        entity_id: str,
    ) -> bool:
        return entity_id in self._storage

    def clear(self) -> None:
        self._storage.clear()