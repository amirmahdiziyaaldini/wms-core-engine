from datetime import date

from app.domain.models.batch import Batch
from app.strategies.stock_allocation_strategy import StockAllocationStrategy


class FIFOStockAllocationStrategy(StockAllocationStrategy):
    def allocate(
        self,
        batches: list[Batch],
        quantity: int,
        reference_date: date | None = None,
    ) -> dict[str, int]:
        if not isinstance(batches, list):
            raise ValueError("Batches must be a list")

        if not isinstance(quantity, int) or isinstance(quantity, bool):
            raise ValueError("Quantity must be an integer")

        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")

        valid_batches = []

        for batch in batches:
            if not isinstance(batch, Batch):
                raise ValueError("All items must be Batch instances")

            if batch.quantity <= 0:
                continue

            if reference_date is not None and batch.is_expired(reference_date):
                continue

            valid_batches.append(batch)

        valid_batches.sort(
            key=lambda batch: batch.entry_date,
        )

        remaining_quantity = quantity
        allocations: dict[str, int] = {}

        for batch in valid_batches:
            if remaining_quantity == 0:
                break

            allocated_quantity = min(
                batch.quantity,
                remaining_quantity,
            )

            allocations[batch.batch_id] = allocated_quantity
            remaining_quantity -= allocated_quantity

        if remaining_quantity > 0:
            raise ValueError(
                "Insufficient valid stock for allocation"
            )

        return allocations