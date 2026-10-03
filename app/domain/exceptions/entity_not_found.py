from app.domain.exceptions.base import DomainError


class EntityNotFoundError(DomainError):
    def __init__(
        self,
        entity_type: str,
        entity_id: str,
    ):
        self.entity_type = entity_type
        self.entity_id = entity_id

        message = (
            f"{entity_type} not found: {entity_id}"
        )

        super().__init__(message)