from app.domain.exceptions.base import DomainError


class ProductNotFoundError(DomainError):
    def __init__(self, sku: str):
        self.sku = sku
        super().__init__(f"Product not found: {sku}")