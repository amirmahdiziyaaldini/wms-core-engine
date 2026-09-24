from datetime import date, datetime
from decimal import Decimal

import pytest

from app.domain.enums.transfer_status import TransferStatus
from app.domain.enums.warehouse_type import WarehouseType
from app.domain.models.base_product import BaseProduct
from app.domain.models.batch import Batch
from app.domain.models.inventory import Inventory
from app.domain.models.inventory_ledger import InventoryLedger
from app.domain.models.warehouse import Warehouse
from app.services.inventory_service import InventoryService
from app.services.stock_transfer_service import StockTransferService


def create_warehouse(warehouse_id: str, name: str) -> Warehouse:
    return Warehouse(
        warehouse_id=warehouse_id,
        name=name,
        location="Location",
        warehouse_type=WarehouseType.LOCAL,
    )


def create_product(sku: str = "LAPTOP-01") -> BaseProduct:
    return BaseProduct(
        sku=sku,
        name="Laptop",
        barcode="123456789",
        category="Electronics",
        base_price=Decimal("500000"),
    )


def create_batch(
    batch_id: str = "BATCH-001",
    sku: str = "LAPTOP-01",
    quantity: int = 10,
) -> Batch:
    return Batch(
        batch_id=batch_id,
        product=create_product(sku),
        quantity=quantity,
        entry_date=date(2026, 1, 1),
    )


def create_service():
    source_inventory = Inventory(
        create_warehouse("WH-001", "Source Warehouse")
    )

    destination_inventory = Inventory(
        create_warehouse("WH-002", "Destination Warehouse")
    )

    source_inventory.add_batch(
        create_batch(quantity=10)
    )

    ledger = InventoryLedger()

    inventory_service = InventoryService(ledger)

    transfer_service = StockTransferService(
        source_inventory=source_inventory,
        destination_inventory=destination_inventory,
        inventory_service=inventory_service,
    )

    return (
        source_inventory,
        destination_inventory,
        inventory_service,
        transfer_service,
    )


def create_transfer(transfer_service: StockTransferService):
    return transfer_service.create_transfer(
        transfer_id="TR-001",
        items=[
            {
                "sku": "LAPTOP-01",
                "quantity": 5,
            }
        ],
        created_at=datetime(2026, 9, 24, 10, 0, 0),
    )


def test_create_transfer():
    (
        source_inventory,
        destination_inventory,
        inventory_service,
        transfer_service,
    ) = create_service()

    transfer = create_transfer(transfer_service)

    assert transfer.transfer_id == "TR-001"
    assert transfer.source is source_inventory.warehouse
    assert transfer.destination is destination_inventory.warehouse
    assert transfer.status == TransferStatus.CREATED


def test_transfer_same_warehouse_is_rejected():
    warehouse = create_warehouse("WH-001", "Warehouse")

    inventory = Inventory(warehouse)
    ledger = InventoryLedger()
    inventory_service = InventoryService(ledger)

    with pytest.raises(ValueError):
        StockTransferService(
            source_inventory=inventory,
            destination_inventory=Inventory(warehouse),
            inventory_service=inventory_service,
        )


def test_dispatch_changes_status_to_in_transit():
    (
        source_inventory,
        destination_inventory,
        inventory_service,
        transfer_service,
    ) = create_service()

    transfer = create_transfer(transfer_service)

    transfer_service.dispatch(transfer)

    assert transfer.status == TransferStatus.IN_TRANSIT
    assert transfer.dispatched_at is not None


def test_dispatch_decreases_source_available_stock():
    (
        source_inventory,
        destination_inventory,
        inventory_service,
        transfer_service,
    ) = create_service()

    transfer = create_transfer(transfer_service)

    transfer_service.dispatch(transfer)

    assert source_inventory.physical_stock("LAPTOP-01") == 5
    assert source_inventory.available_stock("LAPTOP-01") == 5


def test_dispatch_more_than_available_stock_is_rejected():
    (
        source_inventory,
        destination_inventory,
        inventory_service,
        transfer_service,
    ) = create_service()

    transfer = transfer_service.create_transfer(
        transfer_id="TR-001",
        items=[
            {
                "sku": "LAPTOP-01",
                "quantity": 11,
            }
        ],
        created_at=datetime(2026, 9, 24, 10, 0, 0),
    )

    with pytest.raises(ValueError):
        transfer_service.dispatch(transfer)

    assert source_inventory.physical_stock("LAPTOP-01") == 10


def test_dispatch_records_transfer_out_transaction():
    (
        source_inventory,
        destination_inventory,
        inventory_service,
        transfer_service,
    ) = create_service()

    transfer = create_transfer(transfer_service)

    transfer_service.dispatch(transfer)

    transactions = inventory_service.ledger.transactions

    assert len(transactions) == 1
    assert transactions[0].sku == "LAPTOP-01"
    assert transactions[0].quantity == -5
    assert transactions[0].reference_id == "TR-001"


def test_receive_changes_status_to_completed():
    (
        source_inventory,
        destination_inventory,
        inventory_service,
        transfer_service,
    ) = create_service()

    transfer = create_transfer(transfer_service)

    transfer_service.dispatch(transfer)
    transfer_service.receive(transfer)

    assert transfer.status == TransferStatus.COMPLETED
    assert transfer.received_at is not None


def test_receive_increases_destination_inventory():
    (
        source_inventory,
        destination_inventory,
        inventory_service,
        transfer_service,
    ) = create_service()

    transfer = create_transfer(transfer_service)

    transfer_service.dispatch(transfer)
    transfer_service.receive(transfer)

    assert destination_inventory.physical_stock("LAPTOP-01") == 5
    assert destination_inventory.available_stock("LAPTOP-01") == 5


def test_receive_records_transfer_in_transaction():
    (
        source_inventory,
        destination_inventory,
        inventory_service,
        transfer_service,
    ) = create_service()

    transfer = create_transfer(transfer_service)

    transfer_service.dispatch(transfer)
    transfer_service.receive(transfer)

    transactions = inventory_service.ledger.transactions

    assert len(transactions) == 2
    assert transactions[1].sku == "LAPTOP-01"
    assert transactions[1].quantity == 5
    assert transactions[1].reference_id == "TR-001"


def test_receive_creates_new_batch_in_destination():
    (
        source_inventory,
        destination_inventory,
        inventory_service,
        transfer_service,
    ) = create_service()

    transfer = create_transfer(transfer_service)

    transfer_service.dispatch(transfer)
    transfer_service.receive(transfer)

    assert len(destination_inventory.batches) == 1
    assert destination_inventory.batches[0].quantity == 5
    assert destination_inventory.batches[0].product.sku == "LAPTOP-01"


def test_receive_cannot_be_called_before_dispatch():
    (
        source_inventory,
        destination_inventory,
        inventory_service,
        transfer_service,
    ) = create_service()

    transfer = create_transfer(transfer_service)

    with pytest.raises(ValueError):
        transfer_service.receive(transfer)


def test_dispatch_cannot_be_called_twice():
    (
        source_inventory,
        destination_inventory,
        inventory_service,
        transfer_service,
    ) = create_service()

    transfer = create_transfer(transfer_service)

    transfer_service.dispatch(transfer)

    with pytest.raises(ValueError):
        transfer_service.dispatch(transfer)


def test_receive_cannot_be_called_twice():
    (
        source_inventory,
        destination_inventory,
        inventory_service,
        transfer_service,
    ) = create_service()

    transfer = create_transfer(transfer_service)

    transfer_service.dispatch(transfer)
    transfer_service.receive(transfer)

    with pytest.raises(ValueError):
        transfer_service.receive(transfer)