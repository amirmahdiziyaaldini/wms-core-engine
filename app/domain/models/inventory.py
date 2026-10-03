from datetime import date, datetime

from app.domain.enums.warehouse_type import WarehouseType
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

        if batch.warehouse_id is None:
            batch.warehouse_id = self.warehouse.warehouse_id
        elif batch.warehouse_id != self.warehouse.warehouse_id:
            raise ValueError(
                "Batch warehouse does not match inventory warehouse"
            )

        if any(
            existing.batch_id == batch.batch_id
            for existing in self.batches
        ):
            raise ValueError("Batch ID already exists in inventory")

        self.batches.append(batch)

    def get_physical_stock(self, sku: str) -> int:
        if not isinstance(sku, str):
            raise ValueError("SKU must be a string")

        if not sku.strip():
            raise ValueError("SKU cannot be empty")

        total = 0

        for batch in self.batches:
            if batch.product.sku == sku:
                total += batch.remaining_quantity

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

    def get_available_stock(
        self,
        sku: str,
        reference_date: date | None = None,
    ) -> int:
        if reference_date is not None and (
            isinstance(reference_date, datetime)
            or not isinstance(reference_date, date)
        ):
            raise ValueError("Reference date must be a date")

        if (
            self.warehouse.warehouse_type
            == WarehouseType.SCRAP_QUARANTINE
        ):
            return 0

        physical_stock = 0

        for batch in self.batches:
            if batch.product.sku != sku:
                continue

            if batch.is_expired(reference_date):
                continue

            physical_stock += batch.remaining_quantity

        reserved_stock = self.get_reserved_stock(sku)

        available_stock = physical_stock - reserved_stock

        return max(available_stock, 0)

    def available_stock(
        self,
        sku: str,
        reference_date: date | None = None,
    ) -> int:
        return self.get_available_stock(
            sku,
            reference_date,
        )

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

        return reservation

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

        if reservation.batch_allocations:
            batches_by_id = {
                batch.batch_id: batch
                for batch in self.batches
            }

            allocated_quantity = sum(
                reservation.batch_allocations.values()
            )

            if allocated_quantity != reservation.quantity:
                raise ValueError(
                    "Batch allocations do not match reservation quantity"
                )

            for batch_id, quantity in reservation.batch_allocations.items():
                batch = batches_by_id.get(batch_id)

                if batch is None:
                    raise ValueError(
                        f"Batch {batch_id} not found in inventory"
                    )

                if batch.product.sku != reservation.sku:
                    raise ValueError(
                        "Allocated batch SKU does not match reservation SKU"
                    )

                if batch.warehouse_id != self.warehouse.warehouse_id:
                    raise ValueError(
                        "Allocated batch does not belong to inventory warehouse"
                    )

                if batch.quantity < quantity:
                    raise ValueError(
                        f"Insufficient stock in batch {batch_id}"
                    )

        self.reservations[
            reservation.reservation_id
        ] = reservation

    def release_reservation(
        self,
        reservation_id: str,
    ) -> Reservation:
        if not isinstance(reservation_id, str):
            raise ValueError("Reservation ID must be a string")

        if not reservation_id.strip():
            raise ValueError("Reservation ID cannot be empty")

        if reservation_id not in self.reservations:
            raise ValueError("Reservation not found")

        return self.reservations.pop(reservation_id)