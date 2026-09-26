from datetime import datetime


class Shipment:

    def __init__(
        self,
        shipment_id: str,
        order_id: str,
        warehouse_id: str,
        shipped_at: datetime,
        serial_numbers: list[str] | None = None,
        delivered_at: datetime | None = None,
    ):
        if not isinstance(shipment_id, str):
            raise ValueError(
                "Shipment ID must be a string"
            )

        if not shipment_id.strip():
            raise ValueError(
                "Shipment ID cannot be empty"
            )

        if not isinstance(order_id, str):
            raise ValueError(
                "Order ID must be a string"
            )

        if not order_id.strip():
            raise ValueError(
                "Order ID cannot be empty"
            )

        if not isinstance(warehouse_id, str):
            raise ValueError(
                "Warehouse ID must be a string"
            )

        if not warehouse_id.strip():
            raise ValueError(
                "Warehouse ID cannot be empty"
            )

        if not isinstance(shipped_at, datetime):
            raise ValueError(
                "Shipped at must be a datetime"
            )

        if serial_numbers is not None:
            if not isinstance(serial_numbers, list):
                raise ValueError(
                    "Serial numbers must be a list"
                )

            for serial_number in serial_numbers:
                if not isinstance(serial_number, str):
                    raise ValueError(
                        "Serial number must be a string"
                    )

                if not serial_number.strip():
                    raise ValueError(
                        "Serial number cannot be empty"
                    )

            serial_numbers = serial_numbers.copy()

        if delivered_at is not None:
            if not isinstance(delivered_at, datetime):
                raise ValueError(
                    "Delivered at must be a datetime"
                )

            if delivered_at < shipped_at:
                raise ValueError(
                    "Delivered at cannot be before shipped at"
                )

        self.shipment_id = shipment_id
        self.order_id = order_id
        self.warehouse_id = warehouse_id
        self.shipped_at = shipped_at
        self.delivered_at = delivered_at
        self.serial_numbers = serial_numbers or []

    @property
    def is_delivered(self) -> bool:
        return self.delivered_at is not None

    def mark_as_delivered(
        self,
        delivered_at: datetime,
    ) -> None:
        if not isinstance(delivered_at, datetime):
            raise ValueError(
                "Delivered at must be a datetime"
            )

        if delivered_at < self.shipped_at:
            raise ValueError(
                "Delivered at cannot be before shipped at"
            )

        if self.delivered_at is not None:
            raise ValueError(
                "Shipment is already delivered"
            )

        self.delivered_at = delivered_at