from app.domain.models.inventory_transaction import (
    InventoryTransaction,
)


class InventoryLedger:
    def __init__(self):
        self.transactions: list[InventoryTransaction] = []

    def record(self, transaction: InventoryTransaction):
        if not isinstance(
            transaction,
            InventoryTransaction,
        ):
            raise ValueError(
                "Transaction must be an InventoryTransaction"
            )

        self.transactions.append(transaction)