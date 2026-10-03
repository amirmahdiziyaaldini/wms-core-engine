from datetime import date, datetime
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
        warehouse_id: str | None = None,
        original_quantity: int | None = None,
        remaining_quantity: int | None = None,
        product_sku: str | None = None,
        purchase_price: Decimal | None = None,
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

        if original_quantity is None:
            original_quantity = quantity

        if remaining_quantity is None:
            remaining_quantity = quantity

        if not isinstance(original_quantity, int) or isinstance(
            original_quantity, bool
        ):
            raise ValueError("Original quantity must be an integer")

        if original_quantity <= 0:
            raise ValueError("Original quantity must be greater than zero")

        if not isinstance(remaining_quantity, int) or isinstance(
            remaining_quantity, bool
        ):
            raise ValueError("Remaining quantity must be an integer")

        if remaining_quantity < 0 or remaining_quantity > original_quantity:
            raise ValueError(
                "Remaining quantity must be between zero and original quantity"
            )

        if remaining_quantity > quantity and original_quantity == quantity:
            raise ValueError("Remaining quantity cannot exceed quantity")

        if isinstance(entry_date, datetime) or not isinstance(entry_date, date):
            raise ValueError("Entry date must be a date")

        if expiry_date is not None and (
            isinstance(expiry_date, datetime)
            or not isinstance(expiry_date, date)
        ):
            raise ValueError("Expiry date must be a date")

        if product.expiry_tracking and expiry_date is None:
            raise ValueError("Expiry date is required for perishable products")

        if warehouse_id is not None:
            if not isinstance(warehouse_id, str):
                raise ValueError("Warehouse ID must be a string")

            if not warehouse_id.strip():
                raise ValueError("Warehouse ID cannot be empty")

            warehouse_id = warehouse_id.strip()

        if product_sku is not None:
            if not isinstance(product_sku, str):
                raise ValueError("Product SKU must be a string")

            if not product_sku.strip():
                raise ValueError("Product SKU cannot be empty")

            if product_sku.strip() != product.sku:
                raise ValueError("Product SKU does not match product")

        if unit_cost is not None and purchase_price is not None:
            if unit_cost != purchase_price:
                raise ValueError("Unit cost and purchase price must match")

        if purchase_price is not None:
            unit_cost = purchase_price

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

            if len(serial_numbers) != remaining_quantity:
                raise ValueError(
                    "Number of serial numbers must match quantity"
                )

        self.batch_id = batch_id.strip()
        self.product = product
        self.original_quantity = original_quantity
        self.remaining_quantity = remaining_quantity
        self.entry_date = entry_date
        self.expiry_date = expiry_date
        self.serial_numbers = (
            list(serial_numbers)
            if serial_numbers is not None
            else None
        )
        self.unit_cost = unit_cost
        self.warehouse_id = warehouse_id
        self.product_sku = product.sku

    @property
    def quantity(self) -> int:
        return self.remaining_quantity

    @quantity.setter
    def quantity(self, value: int) -> None:
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError("Quantity must be an integer")

        if value < 0 or value > self.original_quantity:
            raise ValueError(
                "Quantity must be between zero and original quantity"
            )

        if isinstance(self.product, SerializedProduct) and self.serial_numbers is not None:
            if len(self.serial_numbers) != value:
                raise ValueError(
                    "Number of serial numbers must match quantity"
                )

        self.remaining_quantity = value

    @property
    def purchase_price(self) -> Decimal | None:
        return self.unit_cost

    @purchase_price.setter
    def purchase_price(self, value: Decimal | None) -> None:
        if value is not None and not isinstance(value, Decimal):
            raise ValueError("Purchase price must be a Decimal")

        if value is not None and value < Decimal("0"):
            raise ValueError("Purchase price cannot be negative")

        self.unit_cost = value

    def is_expired(
        self,
        reference_date: date | None = None,
    ) -> bool:
        if self.expiry_date is None:
            return False

        if reference_date is None:
            reference_date = date.today()

        if isinstance(reference_date, datetime) or not isinstance(reference_date, date):
            raise ValueError("Reference date must be a date")

        return self.expiry_date < reference_date

    def to_dict(self) -> dict:
        return {
            "type": "Batch",
            "batch_id": self.batch_id,
            "product": self.product.sku,
            "product_sku": self.product_sku,
            "warehouse_id": self.warehouse_id,
            "original_quantity": self.original_quantity,
            "remaining_quantity": self.remaining_quantity,
            "quantity": self.quantity,
            "entry_date": self.entry_date,
            "expiry_date": self.expiry_date,
            "serial_numbers": self.serial_numbers,
            "unit_cost": self.unit_cost,
        }