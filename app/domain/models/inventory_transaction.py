from datetime import datetime

from app.domain.enums.inventory_transaction_type import (
    InventoryTransactionType,
)
from app.domain.models.warehouse import Warehouse


class InventoryTransaction:
    def __init__(
        self,
        timestamp: datetime,
        warehouse: Warehouse,
        sku: str,
        quantity: int,
        transaction_type: InventoryTransactionType,
        reference_id: str,
        batch_id: str | None = None,
        serial_numbers: list[str] | None = None,
    ):
        if not isinstance(timestamp, datetime):
            raise ValueError("Timestamp must be a datetime")

        if not isinstance(warehouse, Warehouse):
            raise ValueError("Warehouse must be a Warehouse")

        if not isinstance(sku, str):
            raise ValueError("SKU must be a string")

        if not sku.strip():
            raise ValueError("SKU cannot be empty")

        if not isinstance(quantity, int) or isinstance(quantity, bool):
            raise ValueError("Quantity must be an integer")

        if quantity == 0:
            raise ValueError("Quantity cannot be zero")

        if not isinstance(
            transaction_type,
            InventoryTransactionType,
        ):
            raise ValueError(
                "Transaction type must be an InventoryTransactionType"
            )

        if not isinstance(reference_id, str):
            raise ValueError("Reference ID must be a string")

        if not reference_id.strip():
            raise ValueError("Reference ID cannot be empty")

        if batch_id is not None:
            if not isinstance(batch_id, str):
                raise ValueError("Batch ID must be a string")

            if not batch_id.strip():
                raise ValueError("Batch ID cannot be empty")

        if serial_numbers is not None:
            if not isinstance(serial_numbers, list):
                raise ValueError("Serial numbers must be a list")

            for serial_number in serial_numbers:
                if not isinstance(serial_number, str):
                    raise ValueError(
                        "Serial number must be a string"
                    )

                if not serial_number.strip():
                    raise ValueError(
                        "Serial number cannot be empty"
                    )

            serial_numbers = list(serial_numbers)

        self.timestamp = timestamp
        self.warehouse = warehouse
        self.sku = sku
        self.quantity = quantity
        self.transaction_type = transaction_type
        self.reference_id = reference_id
        self.batch_id = batch_id
        self.serial_numbers = serial_numbers or []