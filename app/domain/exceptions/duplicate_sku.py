from app.domain.exceptions.base import DomainError

class DuplicateSKUError(DomainError):
    def __init__(self, sku: str):
        self.sku = sku
        super().__init__(f"Duplicate SKU: {sku}")