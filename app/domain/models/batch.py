from datetime import date

from app.domain.models.base_product import BaseProduct


class Batch:
    def __init__(
        self,
        batch_id: str,
        product: BaseProduct,
        quantity: int,
        expiry_date: date | None = None,
    ):
        if not isinstance(batch_id, str):
            raise ValueError("Batch ID must be a string")

        if not batch_id.strip():
            raise ValueError("Batch ID cannot be empty")

        if not isinstance(product, BaseProduct):
            raise ValueError("Product must be a BaseProduct")

        if not isinstance(quantity, int):
            raise ValueError("Quantity must be an integer")

        if quantity <= 0:
            raise ValueError(
                "Quantity must be greater than zero"
            )

        if expiry_date is not None and not isinstance(
            expiry_date,
            date,
        ):
            raise ValueError(
                "Expiry date must be a date"
            )

        if product.expiry_tracking and expiry_date is None:
            raise ValueError(
                "Expiry date is required for perishable products"
            )

        self.batch_id = batch_id
        self.product = product
        self.quantity = quantity
        self.expiry_date = expiry_date

    def is_expired(
        self,
        reference_date: date | None = None,
    ) -> bool:
        if self.expiry_date is None:
            return False

        if reference_date is None:
            reference_date = date.today()

        return self.expiry_date < reference_date