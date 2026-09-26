from app.domain.models.shipment import Shipment


class ShipmentRepository:

    def __init__(self):
        self._shipments: dict[str, Shipment] = {}

    def save(
        self,
        shipment: Shipment,
    ) -> None:
        if not isinstance(shipment, Shipment):
            raise ValueError(
                "Shipment must be a Shipment"
            )

        if shipment.shipment_id in self._shipments:
            raise ValueError(
                f"Shipment already exists: {shipment.shipment_id}"
            )

        self._shipments[
            shipment.shipment_id
        ] = shipment

    def get(
        self,
        shipment_id: str,
    ) -> Shipment | None:
        if not isinstance(shipment_id, str):
            raise ValueError(
                "Shipment ID must be a string"
            )

        return self._shipments.get(
            shipment_id
        )

    def get_by_order_id(
        self,
        order_id: str,
    ) -> list[Shipment]:
        if not isinstance(order_id, str):
            raise ValueError(
                "Order ID must be a string"
            )

        return [
            shipment
            for shipment in self._shipments.values()
            if shipment.order_id == order_id
        ]

    def get_by_serial_number(
        self,
        serial_number: str,
    ) -> list[Shipment]:
        if not isinstance(serial_number, str):
            raise ValueError(
                "Serial number must be a string"
            )

        return [
            shipment
            for shipment in self._shipments.values()
            if serial_number in shipment.serial_numbers
        ]

    def list_all(self) -> list[Shipment]:
        return list(
            self._shipments.values()
        )