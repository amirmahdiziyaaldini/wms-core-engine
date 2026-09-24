from datetime import date, datetime

from app.domain.enums.inventory_transaction_type import (
    InventoryTransactionType,
)
from app.domain.models.inventory import Inventory
from app.domain.models.inventory_ledger import InventoryLedger
from app.domain.models.inventory_transaction import InventoryTransaction
from app.domain.models.warehouse import Warehouse
from app.strategies.fifo_stock_allocation_strategy import (
    FIFOStockAllocationStrategy,
)
from app.strategies.stock_allocation_strategy import StockAllocationStrategy


class InventoryService:
    def __init__(
        self,
        ledger: InventoryLedger,
        allocation_strategy: StockAllocationStrategy | None = None,
    ):
        if not isinstance(ledger, InventoryLedger):
            raise ValueError("Ledger must be an InventoryLedger")

        if allocation_strategy is not None and not isinstance(
            allocation_strategy,
            StockAllocationStrategy,
        ):
            raise ValueError(
                "Allocation strategy must be a StockAllocationStrategy"
            )

        self.ledger = ledger

        if allocation_strategy is None:
            allocation_strategy = FIFOStockAllocationStrategy()

        self.allocation_strategy = allocation_strategy

    def record_transaction(
        self,
        timestamp: datetime,
        warehouse: Warehouse,
        sku: str,
        quantity: int,
        transaction_type: InventoryTransactionType,
        reference_id: str,
        batch_id: str | None = None,
        serial_numbers: list[str] | None = None,
    ) -> InventoryTransaction:
        transaction = InventoryTransaction(
            timestamp=timestamp,
            warehouse=warehouse,
            sku=sku,
            quantity=quantity,
            transaction_type=transaction_type,
            reference_id=reference_id,
            batch_id=batch_id,
            serial_numbers=serial_numbers,
        )

        self.ledger.record(transaction)

        return transaction

    def allocate_stock(
        self,
        inventory: Inventory,
        sku: str,
        quantity: int,
        reference_date: date | None = None,
    ) -> dict[str, int]:
        if not isinstance(inventory, Inventory):
            raise ValueError("Inventory must be an Inventory")

        if not isinstance(sku, str):
            raise ValueError("SKU must be a string")

        if not sku.strip():
            raise ValueError("SKU cannot be empty")

        if not isinstance(quantity, int) or isinstance(quantity, bool):
            raise ValueError("Quantity must be an integer")

        if quantity <= 0:
            raise ValueError(
                "Quantity must be greater than zero"
            )

        if reference_date is not None and not isinstance(
            reference_date,
            date,
        ):
            raise ValueError("Reference date must be a date")

        sku_batches = []

        for batch in inventory.batches:
            if batch.product.sku == sku:
                sku_batches.append(batch)

        if not sku_batches:
            raise ValueError(
                f"No batches found for SKU {sku}"
            )

        return self.allocation_strategy.allocate(
            batches=sku_batches,
            quantity=quantity,
            reference_date=reference_date,
        )

    def consume_reservation(
        self,
        inventory: Inventory,
        reservation_id: str,
        timestamp: datetime,
    ) -> list[str]:
        if not isinstance(inventory, Inventory):
            raise ValueError("Inventory must be an Inventory")

        if not isinstance(reservation_id, str):
            raise ValueError(
                "Reservation ID must be a string"
            )

        if not reservation_id.strip():
            raise ValueError(
                "Reservation ID cannot be empty"
            )

        if not isinstance(timestamp, datetime):
            raise ValueError(
                "Timestamp must be a datetime"
            )

        if reservation_id not in inventory.reservations:
            raise ValueError(
                "Reservation not found"
            )

        reservation = inventory.reservations[reservation_id]

        allocations = reservation.batch_allocations

        if not allocations:
            raise ValueError(
                "Reservation has no batch allocations"
            )

        allocated_quantity = sum(
            allocations.values()
        )

        if allocated_quantity != reservation.quantity:
            raise ValueError(
                "Batch allocations do not match reservation quantity"
            )

        batches_by_id = {
            batch.batch_id: batch
            for batch in inventory.batches
        }

        prepared_operations = []
        shipped_serial_numbers = []

        for batch_id, quantity in allocations.items():
            if batch_id not in batches_by_id:
                raise ValueError(
                    f"Batch {batch_id} not found"
                )

            batch = batches_by_id[batch_id]

            if batch.product.sku != reservation.sku:
                raise ValueError(
                    "Allocated batch SKU does not match reservation SKU"
                )

            if not isinstance(quantity, int) or isinstance(
                quantity,
                bool,
            ):
                raise ValueError(
                    "Allocated quantity must be an integer"
                )

            if quantity <= 0:
                raise ValueError(
                    "Allocated quantity must be greater than zero"
                )

            if batch.quantity < quantity:
                raise ValueError(
                    f"Insufficient stock in batch {batch.batch_id}"
                )

            batch_serial_numbers = []

            if batch.serial_numbers is not None:
                if len(batch.serial_numbers) < quantity:
                    raise ValueError(
                        f"Insufficient serial numbers in batch {batch.batch_id}"
                    )

                batch_serial_numbers = batch.serial_numbers[:quantity]

            prepared_operations.append(
                (
                    batch,
                    quantity,
                    batch_serial_numbers,
                )
            )

        original_quantities = {
            batch.batch_id: batch.quantity
            for batch, _, _ in prepared_operations
        }

        original_serial_numbers = {
            batch.batch_id: (
                list(batch.serial_numbers)
                if batch.serial_numbers is not None
                else None
            )
            for batch, _, _ in prepared_operations
        }

        recorded_transactions = []

        try:
            for batch, quantity, serial_numbers in prepared_operations:
                batch.quantity -= quantity

                if batch.serial_numbers is not None:
                    batch.serial_numbers = batch.serial_numbers[
                        quantity:
                    ]

                transaction = self.record_transaction(
                    timestamp=timestamp,
                    warehouse=inventory.warehouse,
                    sku=reservation.sku,
                    quantity=-quantity,
                    transaction_type=InventoryTransactionType.SHIP,
                    reference_id=reservation.order_id,
                    batch_id=batch.batch_id,
                    serial_numbers=serial_numbers,
                )

                recorded_transactions.append(transaction)
                shipped_serial_numbers.extend(
                    serial_numbers
                )

            inventory.release_reservation(
                reservation.reservation_id
            )

        except Exception:
            for batch in inventory.batches:
                if batch.batch_id in original_quantities:
                    batch.quantity = original_quantities[
                        batch.batch_id
                    ]

                    batch.serial_numbers = original_serial_numbers[
                        batch.batch_id
                    ]

            for transaction in recorded_transactions:
                if transaction in self.ledger.transactions:
                    self.ledger.transactions.remove(
                        transaction
                    )

            raise

        return shipped_serial_numbers