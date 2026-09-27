from dataclasses import dataclass

import pytest

from app.repositories.in_memory_repository import (
    InMemoryRepository,
    NotFoundException,
)


@dataclass
class FakeEntity:
    entity_id: str
    name: str


def create_repository() -> InMemoryRepository[FakeEntity]:
    return InMemoryRepository(lambda entity: entity.entity_id)


def test_save_adds_entity_to_repository():
    repository = create_repository()
    entity = FakeEntity("ID-001", "Laptop")

    result = repository.save(entity)

    assert result is entity
    assert repository.get_by_id("ID-001") is entity


def test_save_updates_existing_entity_with_same_id():
    repository = create_repository()

    first = FakeEntity("ID-001", "Laptop")
    second = FakeEntity("ID-001", "Updated Laptop")

    repository.save(first)
    repository.save(second)

    assert repository.get_by_id("ID-001") is second
    assert repository.list() == [second]


def test_get_by_id_returns_entity():
    repository = create_repository()
    entity = FakeEntity("ID-001", "Laptop")

    repository.save(entity)

    result = repository.get_by_id("ID-001")

    assert result is entity


def test_get_by_id_raises_not_found_exception():
    repository = create_repository()

    with pytest.raises(NotFoundException):
        repository.get_by_id("ID-999")


def test_delete_removes_entity():
    repository = create_repository()
    entity = FakeEntity("ID-001", "Laptop")

    repository.save(entity)
    repository.delete("ID-001")

    assert repository.list() == []


def test_delete_unknown_entity_raises_not_found_exception():
    repository = create_repository()

    with pytest.raises(NotFoundException):
        repository.delete("ID-999")


def test_list_returns_all_entities():
    repository = create_repository()

    first = FakeEntity("ID-001", "Laptop")
    second = FakeEntity("ID-002", "Keyboard")

    repository.save(first)
    repository.save(second)

    result = repository.list()

    assert result == [first, second]


def test_repository_storage_is_not_exposed_directly():
    repository = create_repository()
    entity = FakeEntity("ID-001", "Laptop")

    repository.save(entity)

    assert not hasattr(repository, "storage")
    assert hasattr(repository, "_storage")


def test_save_rejects_none_entity():
    repository = create_repository()

    with pytest.raises(ValueError):
        repository.save(None)


def test_repository_rejects_invalid_entity_id():
    repository = create_repository()

    with pytest.raises(ValueError):
        repository.save(FakeEntity("", "Laptop"))


def test_repository_rejects_empty_lookup_id():
    repository = create_repository()

    with pytest.raises(ValueError):
        repository.get_by_id("")


def test_repository_rejects_empty_delete_id():
    repository = create_repository()

    with pytest.raises(ValueError):
        repository.delete("")