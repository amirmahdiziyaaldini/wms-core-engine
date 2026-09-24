from datetime import date, datetime

from app.domain.enums.inventory_transaction_type import (
    InventoryTransactionType,
)
from app.domain.enums.warehouse_type import WarehouseType
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

    def get_inventory_report(
        self,
        inventory: Inventory,
        sku: str,
        reference_date: date | None = None,
        low_stock_threshold: int | None = None,
    ) -> dict[str, int | str | bool | None]:
        if not isinstance(inventory, Inventory):
            raise ValueError("Inventory must be an Inventory")

        if not isinstance(sku, str):
            raise ValueError("SKU must be a string")

        if not sku.strip():
            raise ValueError("SKU cannot be empty")

        if reference_date is None:
            reference_date = date.today()

        if not isinstance(reference_date, date):
            raise ValueError("Reference date must be a date")

        if low_stock_threshold is not None:
            if not isinstance(
                low_stock_threshold,
                int,
            ) or isinstance(
                low_stock_threshold,
                bool,
            ):
                raise ValueError(
                    "Low stock threshold must be an integer"
                )

            if low_stock_threshold < 0:
                raise ValueError(
                    "Low stock threshold cannot be negative"
                )

        physical = inventory.get_physical_stock(sku)
        reserved = inventory.get_reserved_stock(sku)
        available = inventory.get_available_stock(sku)

        expired = 0

        for batch in inventory.batches:
            if batch.product.sku != sku:
                continue

            if batch.is_expired(reference_date):
                expired += batch.quantity

        quarantine = 0

        if (
            inventory.warehouse.warehouse_type
            == WarehouseType.SCRAP_QUARANTINE
        ):
            quarantine = physical

        in_transit = self._get_in_transit_stock(
            inventory,
            sku,
        )

        low_stock = None

        if low_stock_threshold is not None:
            low_stock = available < low_stock_threshold

        return {
            "warehouse_id": inventory.warehouse.warehouse_id,
            "sku": sku,
            "physical": physical,
            "reserved": reserved,
            "available": available,
            "in_transit": in_transit,
            "expired": expired,
            "quarantine": quarantine,
            "low_stock_threshold": low_stock_threshold,
            "low_stock": low_stock,
        }

    def get_inventory_report_for_all_warehouses(
        self,
        inventories: list[Inventory],
        sku: str,
        reference_date: date | None = None,
        low_stock_threshold: int | None = None,
    ) -> list[dict[str, int | str | bool | None]]:
        if not isinstance(inventories, list):
            raise ValueError(
                "Inventories must be a list"
            )

        for inventory in inventories:
            if not isinstance(inventory, Inventory):
                raise ValueError(
                    "Every inventory must be an Inventory"
                )

        return [
            self.get_inventory_report(
                inventory=inventory,
                sku=sku,
                reference_date=reference_date,
                low_stock_threshold=low_stock_threshold,
            )
            for inventory in inventories
        ]

    def _get_in_transit_stock(
        self,
        inventory: Inventory,
        sku: str,
    ) -> int:
        received_transfer_ids = {
            transaction.reference_id
            for transaction in self.ledger.transactions
            if transaction.transaction_type
            == InventoryTransactionType.TRANSFER_IN
        }

        total = 0

        for transaction in self.ledger.transactions:
            if transaction.transaction_type != (
                InventoryTransactionType.TRANSFER_OUT
            ):
                continue

            if transaction.warehouse != inventory.warehouse:
                continue

            if transaction.sku != sku:
                continue

            if transaction.reference_id in received_transfer_ids:
                continue

            total += abs(transaction.quantity)

        return total