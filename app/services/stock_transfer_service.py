from datetime import datetime

from app.domain.enums.inventory_transaction_type import InventoryTransactionType
from app.domain.enums.transfer_status import TransferStatus
from app.domain.models.batch import Batch
from app.domain.models.inventory import Inventory
from app.domain.models.inventory_transaction import InventoryTransaction
from app.domain.models.inventory_ledger import InventoryLedger
from app.domain.models.stock_transfer import StockTransfer, StockTransferItem
from app.services.inventory_service import InventoryService


class StockTransferService:
    def __init__(
        self,
        source_inventory: Inventory,
        destination_inventory: Inventory,
        inventory_service: InventoryService | None = None,
    ):
        if not isinstance(source_inventory, Inventory):
            raise ValueError("Source inventory must be an Inventory")

        if not isinstance(destination_inventory, Inventory):
            raise ValueError("Destination inventory must be an Inventory")

        if (
            source_inventory.warehouse.warehouse_id
            == destination_inventory.warehouse.warehouse_id
        ):
            raise ValueError("Source and destination warehouses must be different")

        if inventory_service is not None and not isinstance(
            inventory_service, InventoryService
        ):
            raise ValueError("Inventory service must be an InventoryService")

        self.source_inventory = source_inventory
        self.destination_inventory = destination_inventory
        self.inventory_service = inventory_service

    def create_transfer(
        self,
        transfer_id: str,
        items: list[StockTransferItem | dict],
        created_at: datetime,
    ) -> StockTransfer:
        if not isinstance(items, list) or not items:
            raise ValueError("Transfer must contain at least one item")

        normalized_items = []

        for item in items:
            if isinstance(item, StockTransferItem):
                normalized_items.append(item)
            elif isinstance(item, dict):
                normalized_items.append(
                    StockTransferItem(
                        sku=item["sku"],
                        quantity=item["quantity"],
                        batch_allocations=item.get("batch_allocations"),
                    )
                )
            else:
                raise ValueError("Invalid transfer item")

        return StockTransfer(
            transfer_id=transfer_id,
            source=self.source_inventory.warehouse,
            destination=self.destination_inventory.warehouse,
            items=normalized_items,
            created_at=created_at,
            status=TransferStatus.CREATED,
        )

    def dispatch(
        self,
        transfer: StockTransfer,
        timestamp: datetime | None = None,
    ) -> StockTransfer:
        if not isinstance(transfer, StockTransfer):
            raise ValueError("Transfer must be a StockTransfer")

        if timestamp is None:
            timestamp = datetime.now()

        if not isinstance(timestamp, datetime):
            raise ValueError("Timestamp must be a datetime")

        if (
            transfer.source.warehouse_id
            != self.source_inventory.warehouse.warehouse_id
        ):
            raise ValueError("Transfer source does not match source inventory")

        if (
            transfer.destination.warehouse_id
            != self.destination_inventory.warehouse.warehouse_id
        ):
            raise ValueError(
                "Transfer destination does not match destination inventory"
            )

        if transfer.status != TransferStatus.CREATED:
            raise ValueError("Only CREATED transfers can be dispatched")

        if self.inventory_service is None:
            raise ValueError("Inventory service is required")

        original_quantities = {
            batch.batch_id: batch.quantity
            for batch in self.source_inventory.batches
        }

        original_serial_numbers = {
            batch.batch_id: (
                list(batch.serial_numbers)
                if batch.serial_numbers is not None
                else None
            )
            for batch in self.source_inventory.batches
        }

        prepared_items = []

        try:
            for item in transfer.items:
                if (
                    self.source_inventory.get_available_stock(item.sku)
                    < item.quantity
                ):
                    raise ValueError(
                        f"Insufficient available stock for SKU {item.sku}"
                    )

                allocations = self.inventory_service.allocate_stock(
                    self.source_inventory,
                    item.sku,
                    item.quantity,
                    reference_date=timestamp.date(),
                )

                item.batch_allocations = allocations

                for batch_id, quantity in allocations.items():
                    batch = next(
                        (
                            batch
                            for batch in self.source_inventory.batches
                            if batch.batch_id == batch_id
                        ),
                        None,
                    )

                    if batch is None:
                        raise ValueError(
                            f"Batch {batch_id} was not found"
                        )

                    if batch.product.sku != item.sku:
                        raise ValueError(
                            f"Batch {batch_id} does not match SKU {item.sku}"
                        )

                    if batch.quantity < quantity:
                        raise ValueError(
                            f"Insufficient stock in batch {batch_id}"
                        )

                    serial_numbers = None

                    if batch.serial_numbers is not None:
                        if len(batch.serial_numbers) < quantity:
                            raise ValueError(
                                f"Insufficient serial numbers in batch {batch_id}"
                            )

                        serial_numbers = batch.serial_numbers[:quantity]
                        batch.serial_numbers = batch.serial_numbers[quantity:]

                    batch.quantity -= quantity

                    prepared_items.append(
                        (
                            item.sku,
                            batch,
                            quantity,
                            serial_numbers,
                        )
                    )

            ledger = self.inventory_service.ledger

            for sku, batch, quantity, serial_numbers in prepared_items:
                ledger.record(
                    InventoryTransaction(
                        timestamp=timestamp,
                        warehouse=self.source_inventory.warehouse,
                        sku=sku,
                        quantity=-quantity,
                        transaction_type=InventoryTransactionType.TRANSFER_OUT,
                        reference_id=transfer.transfer_id,
                        batch_id=batch.batch_id,
                        serial_numbers=serial_numbers,
                    )
                )

            transfer.dispatched_at = timestamp
            transfer.status = TransferStatus.IN_TRANSIT

            return transfer

        except Exception:
            for batch in self.source_inventory.batches:
                if batch.batch_id in original_quantities:
                    batch.quantity = original_quantities[batch.batch_id]

                if batch.batch_id in original_serial_numbers:
                    serial_numbers = original_serial_numbers[batch.batch_id]

                    if serial_numbers is None:
                        batch.serial_numbers = None
                    else:
                        batch.serial_numbers = list(serial_numbers)

            ledger = self.inventory_service.ledger

            ledger.transactions = [
                transaction
                for transaction in ledger.transactions
                if transaction.reference_id != transfer.transfer_id
            ]

            for item in transfer.items:
                item.batch_allocations = {}

            raise

    def receive(
        self,
        transfer: StockTransfer,
        timestamp: datetime | None = None,
    ) -> StockTransfer:
        if not isinstance(transfer, StockTransfer):
            raise ValueError("Transfer must be a StockTransfer")

        if timestamp is None:
            timestamp = datetime.now()

        if not isinstance(timestamp, datetime):
            raise ValueError("Timestamp must be a datetime")

        if transfer.status != TransferStatus.IN_TRANSIT:
            raise ValueError("Only IN_TRANSIT transfers can be received")

        created_batches = []
        recorded_transactions = []

        try:
            for item in transfer.items:
                if not item.batch_allocations:
                    raise ValueError(
                        f"No batch allocation found for SKU {item.sku}"
                    )

                for batch_id, quantity in item.batch_allocations.items():
                    source_batch = next(
                        (
                            batch
                            for batch in self.source_inventory.batches
                            if batch.batch_id == batch_id
                        ),
                        None,
                    )

                    if source_batch is None:
                        raise ValueError(
                            f"Source batch {batch_id} was not found"
                        )

                    serial_numbers = None

                    if source_batch.serial_numbers is not None:
                        serial_numbers = []

                    destination_batch = Batch(
                        batch_id=f"{transfer.transfer_id}-{batch_id}",
                        product=source_batch.product,
                        quantity=quantity,
                        entry_date=timestamp.date(),
                        expiry_date=source_batch.expiry_date,
                        serial_numbers=serial_numbers,
                    )

                    self.destination_inventory.add_batch(
                        destination_batch
                    )

                    created_batches.append(destination_batch)

                    transaction = InventoryTransaction(
                        timestamp=timestamp,
                        warehouse=self.destination_inventory.warehouse,
                        sku=item.sku,
                        quantity=quantity,
                        transaction_type=InventoryTransactionType.TRANSFER_IN,
                        reference_id=transfer.transfer_id,
                        batch_id=destination_batch.batch_id,
                        serial_numbers=serial_numbers,
                    )

                    self.inventory_service.ledger.record(transaction)
                    recorded_transactions.append(transaction)

            transfer.received_at = timestamp
            transfer.status = TransferStatus.RECEIVED
            transfer.status = TransferStatus.COMPLETED

            return transfer

        except Exception:
            for batch in created_batches:
                if batch in self.destination_inventory.batches:
                    self.destination_inventory.batches.remove(batch)

            self.inventory_service.ledger.transactions = [
                transaction
                for transaction in self.inventory_service.ledger.transactions
                if transaction not in recorded_transactions
            ]

            raise