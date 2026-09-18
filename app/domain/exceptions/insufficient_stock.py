from app.domain.exceptions.base import DomainError


class InsufficientStockError(DomainError):
    def __init__(self, sku: str, requested: int, available: int):
        self.sku = sku
        self.requested = requested
        self.available = available

        super().__init__(
            f"Insufficient stock for SKU {sku}: "
            f"requested {requested}, available {available}"
        )