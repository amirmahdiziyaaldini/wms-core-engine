from app.domain.models.serialized_product import SerializedProduct


class SerializedUnit:
    def __init__(
        self,
        serial_number: str,
        product: SerializedProduct,
        location: str | None = None,
        status: str = "available",
    ):
        if not isinstance(serial_number, str):
            raise ValueError("Serial number must be a string")

        if not serial_number.strip():
            raise ValueError("Serial number cannot be empty")

        if not isinstance(product, SerializedProduct):
            raise ValueError(
                "Product must be a SerializedProduct"
            )

        if location is not None:
            if not isinstance(location, str):
                raise ValueError("Location must be a string")

            if not location.strip():
                raise ValueError("Location cannot be empty")

        if not isinstance(status, str):
            raise ValueError("Status must be a string")

        if not status.strip():
            raise ValueError("Status cannot be empty")

        self.serial_number = serial_number
        self.product = product
        self.location = location
        self.status = status