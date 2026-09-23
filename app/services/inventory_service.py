from datetime import datetime

from app.domain.enums.inventory_transaction_type import (
    InventoryTransactionType,
)
from app.domain.models.inventory_ledger import InventoryLedger
from app.domain.models.inventory_transaction import (
    InventoryTransaction,
)
from app.domain.models.warehouse import Warehouse


class InventoryService:
    def __init__(self, ledger: InventoryLedger):
        if not isinstance(ledger, InventoryLedger):
            raise ValueError(
                "Ledger must be an InventoryLedger"
            )

        self.ledger = ledger

    def record_transaction(
        self,
        timestamp: datetime,
        warehouse: Warehouse,
        sku: str,
        quantity: int,
        transaction_type: InventoryTransactionType,
        reference_id: str,
    ):
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