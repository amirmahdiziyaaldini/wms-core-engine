from app.domain.models.serialized_product import SerializedProduct


class SerializedUnit:
    def __init__(
        self,
        serial_number: str,
        product: SerializedProduct,
    ):
        if not isinstance(serial_number, str):
            raise ValueError("Serial number must be a string")

        if not serial_number.strip():
            raise ValueError("Serial number cannot be empty")

        if not isinstance(product, SerializedProduct):
            raise ValueError(
                "Product must be a SerializedProduct"
            )

        self.serial_number = serial_number
        self.product = product