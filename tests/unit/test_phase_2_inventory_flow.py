from datetime import date, datetime
from decimal import Decimal

import pytest

from app.domain.enums.inventory_transaction_type import (
    InventoryTransactionType,
)
from app.domain.enums.transfer_status import TransferStatus
from app.domain.enums.warehouse_type import WarehouseType
from app.domain.models.base_product import BaseProduct
from app.domain.models.batch import Batch
from app.domain.models.inventory import Inventory
from app.domain.models.inventory_ledger import InventoryLedger
from app.domain.models.reservation import Reservation
from app.domain.models.warehouse import Warehouse
from app.services.inventory_service import InventoryService
from app.services.stock_transfer_service import StockTransferService


def create_product(sku="SKU-001"):
    return BaseProduct(
        sku=sku,
        name="Product",
        barcode=f"BAR-{sku}",
        category="General",
        base_price=Decimal("100"),
    )


def create_warehouse(
    warehouse_id="WH-001",
    warehouse_type=WarehouseType.CENTRAL,
):
    return Warehouse(
        warehouse_id=warehouse_id,
        name=warehouse_id,
        location="Tehran",
        warehouse_type=warehouse_type,
    )


def create_batch(
    batch_id="BATCH-001",
    quantity=10,
    entry_date=date(2026, 9, 1),
    expiry_date=None,
):
    return Batch(
        batch_id=batch_id,
        product=create_product(),
        quantity=quantity,
        entry_date=entry_date,
        expiry_date=expiry_date,
        unit_cost=Decimal("70"),
    )


def test_batch_keeps_original_and_remaining_quantity():
    batch = create_batch(quantity=10)

    assert batch.original_quantity == 10
    assert batch.remaining_quantity == 10
    assert batch.quantity == 10
    assert batch.purchase_price == Decimal("70")

    batch.quantity = 6

    assert batch.remaining_quantity == 6
    assert batch.original_quantity == 10


def test_inventory_assigns_batch_warehouse_id():
    inventory = Inventory(
        create_warehouse("WH-001")
    )

    batch = create_batch()

    inventory.add_batch(batch)

    assert batch.warehouse_id == "WH-001"
    assert batch.product_sku == "SKU-001"


def test_inventory_rejects_batch_from_another_warehouse():
    inventory = Inventory(
        create_warehouse("WH-001")
    )

    batch = create_batch()
    batch.warehouse_id = "WH-002"

    with pytest.raises(ValueError):
        inventory.add_batch(batch)


def test_expired_stock_is_not_available():
    inventory = Inventory(
        create_warehouse()
    )

    inventory.add_batch(
        create_batch(
            quantity=10,
            expiry_date=date(2026, 9, 1),
        )
    )

    assert inventory.get_physical_stock(
        "SKU-001"
    ) == 10

    assert inventory.get_available_stock(
        "SKU-001",
        reference_date=date(2026, 9, 28),
    ) == 0


def test_receive_records_receive_transaction():
    inventory = Inventory(
        create_warehouse()
    )

    ledger = InventoryLedger()
    service = InventoryService(ledger)
    batch = create_batch(quantity=5)

    service.receive(
        inventory=inventory,
        batch=batch,
        reference_id="REC-001",
        timestamp=datetime(
            2026,
            9,
            28,
            10,
            0,
        ),
    )

    assert inventory.get_physical_stock(
        "SKU-001"
    ) == 5

    assert len(
        ledger.transactions
    ) == 1

    assert (
        ledger.transactions[0].transaction_type
        == InventoryTransactionType.RECEIVE
    )

    assert (
        ledger.transactions[0].reference_id
        == "REC-001"
    )


def test_reserve_and_release_record_ledger_transactions():
    inventory = Inventory(
        create_warehouse()
    )

    inventory.add_batch(
        create_batch(quantity=10)
    )

    ledger = InventoryLedger()
    service = InventoryService(ledger)

    reservation = Reservation(
        reservation_id="RES-001",
        order_id="ORD-001",
        order_item_id="ITEM-001",
        sku="SKU-001",
        quantity=4,
    )

    service.reserve_reservation(
        inventory=inventory,
        reservation=reservation,
        timestamp=datetime(
            2026,
            9,
            28,
            10,
            0,
        ),
    )

    service.release_reservation(
        inventory=inventory,
        reservation_id="RES-001",
        timestamp=datetime(
            2026,
            9,
            28,
            10,
            5,
        ),
    )

    assert [
        transaction.transaction_type
        for transaction in ledger.transactions
    ] == [
        InventoryTransactionType.RESERVE,
        InventoryTransactionType.RELEASE_RESERVATION,
    ]

    assert (
        ledger.transactions[0].quantity
        == 4
    )

    assert (
        ledger.transactions[1].quantity
        == -4
    )


def test_transfer_does_not_add_destination_stock_before_receive():
    source = Inventory(
        create_warehouse("WH-001")
    )

    destination = Inventory(
        create_warehouse(
            "WH-002",
            WarehouseType.LOCAL,
        )
    )

    source.add_batch(
        create_batch(quantity=10)
    )

    ledger = InventoryLedger()
    inventory_service = InventoryService(ledger)

    transfer_service = StockTransferService(
        source_inventory=source,
        destination_inventory=destination,
        inventory_service=inventory_service,
    )

    transfer = transfer_service.create_transfer(
        transfer_id="TR-001",
        items=[
            {
                "sku": "SKU-001",
                "quantity": 4,
            }
        ],
        created_at=datetime(
            2026,
            9,
            28,
            10,
            0,
        ),
    )

    transfer_service.dispatch(
        transfer,
        timestamp=datetime(
            2026,
            9,
            28,
            10,
            5,
        ),
    )

    assert (
        transfer.status
        == TransferStatus.IN_TRANSIT
    )

    assert (
        source.get_available_stock("SKU-001")
        == 6
    )

    assert (
        destination.get_physical_stock("SKU-001")
        == 0
    )

    transfer_service.receive(
        transfer,
        timestamp=datetime(
            2026,
            9,
            28,
            11,
            0,
        ),
    )

    assert (
        transfer.status
        == TransferStatus.COMPLETED
    )

    assert (
        destination.get_physical_stock("SKU-001")
        == 4
    )