from dataclasses import dataclass

import pytest

from app.domain.exceptions.entity_not_found import EntityNotFoundError
from app.repositories.in_memory_repository import InMemoryRepository


@dataclass
class FakeEntity:
    entity_id: str
    name: str


def create_repository() -> InMemoryRepository[FakeEntity]:
    return InMemoryRepository()


def test_save_adds_entity_to_repository():
    repository = create_repository()
    entity = FakeEntity("ID-001", "Laptop")

    result = repository.save("ID-001", entity)

    assert result is entity
    assert repository.get("ID-001") is entity


def test_save_rejects_duplicate_entity_id():
    repository = create_repository()

    first = FakeEntity("ID-001", "Laptop")
    second = FakeEntity("ID-001", "Updated Laptop")

    repository.save("ID-001", first)

    with pytest.raises(ValueError):
        repository.save("ID-001", second)

    assert repository.get("ID-001") is first


def test_get_returns_entity():
    repository = create_repository()
    entity = FakeEntity("ID-001", "Laptop")

    repository.save("ID-001", entity)

    result = repository.get("ID-001")

    assert result is entity


def test_get_missing_entity_raises_entity_not_found_error():
    repository = create_repository()

    with pytest.raises(EntityNotFoundError) as exc_info:
        repository.get("ID-999")

    assert exc_info.value.entity_type == "InMemoryRepository"
    assert exc_info.value.entity_id == "ID-999"
    assert str(exc_info.value) == "InMemoryRepository not found: ID-999"


def test_delete_removes_entity():
    repository = create_repository()
    entity = FakeEntity("ID-001", "Laptop")

    repository.save("ID-001", entity)
    repository.delete("ID-001")

    assert repository.list() == []


def test_delete_missing_entity_raises_entity_not_found_error():
    repository = create_repository()

    with pytest.raises(EntityNotFoundError) as exc_info:
        repository.delete("ID-999")

    assert exc_info.value.entity_type == "InMemoryRepository"
    assert exc_info.value.entity_id == "ID-999"


def test_list_returns_all_entities():
    repository = create_repository()

    first = FakeEntity("ID-001", "Laptop")
    second = FakeEntity("ID-002", "Keyboard")

    repository.save("ID-001", first)
    repository.save("ID-002", second)

    result = repository.list()

    assert result == [first, second]


def test_repository_storage_is_not_exposed_directly():
    repository = create_repository()

    assert not hasattr(repository, "storage")
    assert hasattr(repository, "_storage")


def test_save_rejects_none_entity():
    repository = create_repository()

    with pytest.raises(ValueError):
        repository.save("ID-001", None)


def test_save_rejects_invalid_entity_id():
    repository = create_repository()
    entity = FakeEntity("ID-001", "Laptop")

    with pytest.raises(ValueError):
        repository.save("", entity)


def test_get_rejects_empty_entity_id():
    repository = create_repository()

    with pytest.raises(ValueError):
        repository.get("")


def test_delete_rejects_empty_entity_id():
    repository = create_repository()

    with pytest.raises(ValueError):
        repository.delete("")


def test_exists_returns_true_for_existing_entity():
    repository = create_repository()
    entity = FakeEntity("ID-001", "Laptop")

    repository.save("ID-001", entity)

    assert repository.exists("ID-001") is True


def test_exists_returns_false_for_missing_entity():
    repository = create_repository()

    assert repository.exists("ID-999") is False


def test_clear_removes_all_entities():
    repository = create_repository()

    repository.save("ID-001", FakeEntity("ID-001", "Laptop"))
    repository.save("ID-002", FakeEntity("ID-002", "Keyboard"))

    repository.clear()

    assert repository.list() == []
    assert repository.exists("ID-001") is False
    assert repository.exists("ID-002") is False