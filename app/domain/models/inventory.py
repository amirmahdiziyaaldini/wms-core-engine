from app.domain.models.batch import Batch
from app.domain.models.warehouse import Warehouse


class Inventory:
    def __init__(self, warehouse: Warehouse):
        if not isinstance(warehouse, Warehouse):
            raise ValueError(
                "Warehouse must be a Warehouse"
            )

        self.warehouse = warehouse
        self.batches: list[Batch] = []
        self.reservations: dict[str, dict[str, int]] = {}

    def add_batch(self, batch: Batch):
        if not isinstance(batch, Batch):
            raise ValueError(
                "Batch must be a Batch"
            )

        self.batches.append(batch)

    def get_physical_stock(self, sku: str) -> int:
        self._validate_sku(sku)

        total = 0

        for batch in self.batches:
            if batch.product.sku == sku:
                total += batch.quantity

        return total

    def get_reserved_stock(self, sku: str) -> int:
        self._validate_sku(sku)

        total = 0

        for reservation in self.reservations.values():
            total += reservation.get(sku, 0)

        return total

    def get_available_stock(self, sku: str) -> int:
        self._validate_sku(sku)

        physical_stock = self.get_physical_stock(sku)
        reserved_stock = self.get_reserved_stock(sku)

        available_stock = physical_stock - reserved_stock

        if available_stock < 0:
            raise ValueError(
                "Available stock cannot be negative"
            )

        return available_stock

    def reserve(
        self,
        reservation_id: str,
        sku: str,
        quantity: int,
    ):
        self._validate_reservation_id(reservation_id)
        self._validate_sku(sku)

        if not isinstance(quantity, int) or isinstance(
            quantity,
            bool,
        ):
            raise ValueError(
                "Reservation quantity must be an integer"
            )

        if quantity <= 0:
            raise ValueError(
                "Reservation quantity must be greater than zero"
            )

        if reservation_id in self.reservations:
            raise ValueError(
                "Reservation ID already exists"
            )

        available_stock = self.get_available_stock(sku)

        if quantity > available_stock:
            raise ValueError(
                "Insufficient available stock"
            )

        self.reservations[reservation_id] = {
            sku: quantity
        }

    def release_reservation(
        self,
        reservation_id: str,
    ):
        self._validate_reservation_id(reservation_id)

        if reservation_id not in self.reservations:
            raise ValueError(
                "Reservation not found"
            )

        del self.reservations[reservation_id]

    @staticmethod
    def _validate_sku(sku: str):
        if not isinstance(sku, str):
            raise ValueError(
                "SKU must be a string"
            )

        if not sku.strip():
            raise ValueError(
                "SKU cannot be empty"
            )

    @staticmethod
    def _validate_reservation_id(
        reservation_id: str,
    ):
        if not isinstance(reservation_id, str):
            raise ValueError(
                "Reservation ID must be a string"
            )

        if not reservation_id.strip():
            raise ValueError(
                "Reservation ID cannot be empty"
            )