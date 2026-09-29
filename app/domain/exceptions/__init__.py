from app.domain.exceptions.base import DomainError
from app.domain.exceptions.entity_not_found import EntityNotFoundError

__all__ = [
    "DomainError",
    "EntityNotFoundError",
]