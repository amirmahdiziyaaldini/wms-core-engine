from datetime import datetime


class ReturnReceipt:

    def __init__(
        self,
        receipt_id: str,
        return_id: str,
        sku: str,
        quantity: int,
        serial_numbers: list[str] | None = None,
        location: str = "RETURN_QUARANTINE",
        status: str = "received_at_warehouse",
        received_at: datetime | None = None,
    ):
        if not isinstance(receipt_id, str):
            raise ValueError("Receipt ID must be a string")

        if not receipt_id.strip():
            raise ValueError("Receipt ID cannot be empty")

        if not isinstance(return_id, str):
            raise ValueError("Return ID must be a string")

        if not return_id.strip():
            raise ValueError("Return ID cannot be empty")

        if not isinstance(sku, str):
            raise ValueError("SKU must be a string")

        if not sku.strip():
            raise ValueError("SKU cannot be empty")

        if isinstance(quantity, bool) or not isinstance(quantity, int):
            raise ValueError("Quantity must be an integer")

        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        if not isinstance(location, str):
            raise ValueError("Location must be a string")

        if not location.strip():
            raise ValueError("Location cannot be empty")

        if not isinstance(status, str):
            raise ValueError("Status must be a string")

        if not status.strip():
            raise ValueError("Status cannot be empty")

        if serial_numbers is not None:
            if not isinstance(serial_numbers, list):
                raise ValueError("Serial numbers must be a list")

            if len(serial_numbers) != quantity:
                raise ValueError(
                    "Number of serial numbers must match quantity"
                )

            seen_serials = set()

            for serial_number in serial_numbers:
                if not isinstance(serial_number, str):
                    raise ValueError(
                        "Serial number must be a string"
                    )

                if not serial_number.strip():
                    raise ValueError(
                        "Serial number cannot be empty"
                    )

                if serial_number in seen_serials:
                    raise ValueError(
                        "Serial numbers must be unique"
                    )

                seen_serials.add(serial_number)

        if received_at is not None and not isinstance(
            received_at,
            datetime,
        ):
            raise ValueError(
                "Received at must be a datetime"
            )

        self.receipt_id = receipt_id
        self.return_id = return_id
        self.sku = sku
        self.quantity = quantity
        self.serial_numbers = serial_numbers
        self.location = location
        self.status = status
        self.received_at = (
            received_at
            if received_at is not None
            else datetime.now()
        )