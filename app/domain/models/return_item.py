class ReturnItem:

    def __init__(
        self,
        sku: str,
        quantity: int,
        serial_numbers: list[str] | None = None,
    ):
        if not isinstance(sku, str):
            raise ValueError("SKU must be a string")

        if not sku.strip():
            raise ValueError("SKU cannot be empty")

        if isinstance(quantity, bool) or not isinstance(quantity, int):
            raise ValueError("Quantity must be an integer")

        if quantity <= 0:
            raise ValueError("Quantity must be positive")

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
                    raise ValueError("Serial number must be a string")

                if not serial_number.strip():
                    raise ValueError("Serial number cannot be empty")

                if serial_number in seen_serials:
                    raise ValueError("Serial numbers must be unique")

                seen_serials.add(serial_number)

        self.sku = sku
        self.quantity = quantity
        self.serial_numbers = serial_numbers