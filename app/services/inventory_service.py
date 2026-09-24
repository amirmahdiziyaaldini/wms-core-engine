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
    ) -> InventoryTransaction:
        transaction = InventoryTransaction(
            timestamp=timestamp,
            warehouse=warehouse,
            sku=sku,
            quantity=quantity,
            transaction_type=transaction_type,
            reference_id=reference_id,
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
            raise ValueError("Quantity must be greater than zero")

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