from datetime import datetime

from app.domain.enums.transfer_status import TransferStatus
from app.domain.models.warehouse import Warehouse


class StockTransferItem:
    def __init__(
        self,
        sku: str,
        quantity: int,
        batch_allocations: dict[str, int] | None = None,
    ):
        if not isinstance(sku, str) or not sku.strip():
            raise ValueError("SKU cannot be empty")

        if not isinstance(quantity, int) or isinstance(quantity, bool):
            raise ValueError("Quantity must be an integer")

        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")

        if batch_allocations is not None:
            if not isinstance(batch_allocations, dict):
                raise ValueError("Batch allocations must be a dictionary")

            for batch_id, batch_quantity in batch_allocations.items():
                if (
                    not isinstance(batch_id, str)
                    or not batch_id.strip()
                    or not isinstance(batch_quantity, int)
                    or isinstance(batch_quantity, bool)
                    or batch_quantity <= 0
                ):
                    raise ValueError("Invalid batch allocation")

            if sum(batch_allocations.values()) != quantity:
                raise ValueError("Batch allocations must equal item quantity")

        self.sku = sku.strip()
        self.quantity = quantity
        self.batch_allocations = batch_allocations or {}


class StockTransfer:
    def __init__(
        self,
        transfer_id: str,
        source: Warehouse,
        destination: Warehouse,
        items: list[StockTransferItem],
        created_at: datetime,
        dispatched_at: datetime | None = None,
        received_at: datetime | None = None,
        status: TransferStatus | None = None,
    ):
        if not isinstance(transfer_id, str) or not transfer_id.strip():
            raise ValueError("Transfer ID cannot be empty")

        if not isinstance(source, Warehouse):
            raise ValueError("Source must be a Warehouse")

        if not isinstance(destination, Warehouse):
            raise ValueError("Destination must be a Warehouse")

        if source.warehouse_id == destination.warehouse_id:
            raise ValueError("Source and destination warehouses must be different")

        if not isinstance(items, list) or not items:
            raise ValueError("Transfer must contain at least one item")

        if any(not isinstance(item, StockTransferItem) for item in items):
            raise ValueError("All transfer items must be StockTransferItem")

        if not isinstance(created_at, datetime):
            raise ValueError("Created at must be a datetime")

        if dispatched_at is not None and not isinstance(dispatched_at, datetime):
            raise ValueError("Dispatched at must be a datetime")

        if received_at is not None and not isinstance(received_at, datetime):
            raise ValueError("Received at must be a datetime")

        if status is None:
            status = TransferStatus.CREATED

        if not isinstance(status, TransferStatus):
            raise ValueError("Invalid transfer status")

        self.transfer_id = transfer_id.strip()
        self.source = source
        self.destination = destination
        self.items = items
        self.created_at = created_at
        self.dispatched_at = dispatched_at
        self.received_at = received_at
        self.status = status