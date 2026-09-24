from app.domain.models.batch import Batch
from app.domain.models.reservation import Reservation
from app.domain.models.warehouse import Warehouse


class Inventory:
    def __init__(self, warehouse: Warehouse):
        if not isinstance(warehouse, Warehouse):
            raise ValueError("Warehouse must be a Warehouse")

        self.warehouse = warehouse
        self.batches: list[Batch] = []
        self.reservations: dict[str, Reservation] = {}

    def add_batch(self, batch: Batch):
        if not isinstance(batch, Batch):
            raise ValueError("Batch must be a Batch")

        self.batches.append(batch)

    def get_physical_stock(self, sku: str) -> int:
        if not isinstance(sku, str):
            raise ValueError("SKU must be a string")

        if not sku.strip():
            raise ValueError("SKU cannot be empty")

        total = 0

        for batch in self.batches:
            if batch.product.sku == sku:
                total += batch.quantity

        return total

    def physical_stock(self, sku: str) -> int:
        return self.get_physical_stock(sku)

    def get_reserved_stock(self, sku: str) -> int:
        if not isinstance(sku, str):
            raise ValueError("SKU must be a string")

        if not sku.strip():
            raise ValueError("SKU cannot be empty")

        total = 0

        for reservation in self.reservations.values():
            if reservation.sku == sku:
                total += reservation.quantity

        return total

    def get_available_stock(self, sku: str) -> int:
        physical_stock = self.get_physical_stock(sku)
        reserved_stock = self.get_reserved_stock(sku)

        available_stock = physical_stock - reserved_stock

        if available_stock < 0:
            raise ValueError("Available stock cannot be negative")

        return available_stock

    def available_stock(self, sku: str) -> int:
        return self.get_available_stock(sku)

    def reserve(
        self,
        reservation_id: str,
        sku: str,
        quantity: int,
    ):
        if not isinstance(reservation_id, str):
            raise ValueError("Reservation ID must be a string")

        if not reservation_id.strip():
            raise ValueError("Reservation ID cannot be empty")

        if not isinstance(sku, str):
            raise ValueError("SKU must be a string")

        if not sku.strip():
            raise ValueError("SKU cannot be empty")

        if not isinstance(quantity, int) or isinstance(quantity, bool):
            raise ValueError("Quantity must be an integer")

        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")

        if reservation_id in self.reservations:
            raise ValueError("Reservation ID already exists")

        available_stock = self.get_available_stock(sku)

        if quantity > available_stock:
            raise ValueError("Insufficient available stock")

        reservation = Reservation(
            reservation_id=reservation_id,
            order_id=reservation_id,
            order_item_id=reservation_id,
            sku=sku,
            quantity=quantity,
        )

        self.reservations[reservation_id] = reservation

    def reserve_reservation(
        self,
        reservation: Reservation,
    ):
        if not isinstance(reservation, Reservation):
            raise ValueError("Reservation must be a Reservation")

        if reservation.reservation_id in self.reservations:
            raise ValueError("Reservation ID already exists")

        available_stock = self.get_available_stock(
            reservation.sku
        )

        if reservation.quantity > available_stock:
            raise ValueError("Insufficient available stock")

        self.reservations[
            reservation.reservation_id
        ] = reservation

    def release_reservation(
        self,
        reservation_id: str,
    ):
        if not isinstance(reservation_id, str):
            raise ValueError("Reservation ID must be a string")

        if not reservation_id.strip():
            raise ValueError("Reservation ID cannot be empty")

        if reservation_id not in self.reservations:
            raise ValueError("Reservation not found")

        del self.reservations[reservation_id]