from datetime import date
from decimal import Decimal

from app.domain.models.base_product import BaseProduct
from app.domain.models.serialized_product import SerializedProduct


class Batch:
    def __init__(
        self,
        batch_id: str,
        product: BaseProduct,
        quantity: int,
        entry_date: date,
        expiry_date: date | None = None,
        serial_numbers: list[str] | None = None,
        unit_cost: Decimal | None = None,
    ):
        if not isinstance(batch_id, str):
            raise ValueError("Batch ID must be a string")

        if not batch_id.strip():
            raise ValueError("Batch ID cannot be empty")

        if not isinstance(product, BaseProduct):
            raise ValueError("Product must be a BaseProduct")

        if not isinstance(quantity, int) or isinstance(quantity, bool):
            raise ValueError("Quantity must be an integer")

        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")

        if not isinstance(entry_date, date):
            raise ValueError("Entry date must be a date")

        if expiry_date is not None and not isinstance(expiry_date, date):
            raise ValueError("Expiry date must be a date")

        if product.expiry_tracking and expiry_date is None:
            raise ValueError("Expiry date is required for perishable products")

        if unit_cost is not None:
            if not isinstance(unit_cost, Decimal):
                raise ValueError("Unit cost must be a Decimal")

            if unit_cost < Decimal("0"):
                raise ValueError("Unit cost cannot be negative")

        if serial_numbers is not None:
            if not isinstance(serial_numbers, list):
                raise ValueError("Serial numbers must be a list")

            for serial_number in serial_numbers:
                if not isinstance(serial_number, str):
                    raise ValueError("Serial number must be a string")

                if not serial_number.strip():
                    raise ValueError("Serial number cannot be empty")

            if len(serial_numbers) != len(set(serial_numbers)):
                raise ValueError("Serial numbers must be unique")

        if isinstance(product, SerializedProduct):
            if serial_numbers is None:
                raise ValueError(
                    "Serial numbers are required for serialized products"
                )

            if len(serial_numbers) != quantity:
                raise ValueError(
                    "Number of serial numbers must match quantity"
                )

        self.batch_id = batch_id
        self.product = product
        self.quantity = quantity
        self.entry_date = entry_date
        self.expiry_date = expiry_date
        self.serial_numbers = serial_numbers
        self.unit_cost = unit_cost

    def is_expired(self, reference_date: date | None = None) -> bool:
        if self.expiry_date is None:
            return False

        if reference_date is None:
            reference_date = date.today()

        return self.expiry_date < reference_date