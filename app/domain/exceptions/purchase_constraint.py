from app.domain.exceptions.base import DomainError

class PurchaseConstraintViolation(DomainError):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)