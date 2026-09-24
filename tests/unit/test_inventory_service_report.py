from datetime import date, datetime
from decimal import Decimal

import pytest

from app.domain.enums.inventory_transaction_type import (
    InventoryTransactionType,
)
from app.domain.enums.warehouse_type import WarehouseType
from app.domain.models.base_product import BaseProduct
from app.domain.models.batch import Batch
from app.domain.models.inventory import Inventory
from app.domain.models.inventory_ledger import InventoryLedger
from app.domain.models.inventory_transaction import InventoryTransaction
from app.domain.models.warehouse import Warehouse
from app.services.inventory_service import InventoryService


def create_product():
    return BaseProduct(
        sku="LAPTOP-01",
        name="Laptop",
        barcode="123456789",
        category="Electronics",
        base_price=Decimal("500000"),
    )


def create_batch(
    batch_id: str,
    quantity: int,
    expiry_date: date | None = None,
):
    return Batch(
        batch_id=batch_id,
        product=create_product(),
        quantity=quantity,
        entry_date=date(2026, 1, 1),
        expiry_date=expiry_date,
    )


def create_warehouse(
    warehouse_id: str,
    warehouse_type: WarehouseType = WarehouseType.LOCAL,
):
    return Warehouse(
        warehouse_id=warehouse_id,
        name=warehouse_id,
        location="Tehran",
        warehouse_type=warehouse_type,
    )


def create_inventory(
    warehouse_id: str = "WH-001",
    warehouse_type: WarehouseType = WarehouseType.LOCAL,
):
    return Inventory(
        create_warehouse(
            warehouse_id,
            warehouse_type,
        )
    )


def create_service():
    return InventoryService(
        InventoryLedger()
    )


def test_inventory_report_returns_physical_reserved_available():
    service = create_service()
    inventory = create_inventory()

    inventory.add_batch(
        create_batch(
            batch_id="BATCH-001",
            quantity=10,
        )
    )

    inventory.reserve(
        reservation_id="RES-001",
        sku="LAPTOP-01",
        quantity=3,
    )

    report = service.get_inventory_report(
        inventory=inventory,
        sku="LAPTOP-01",
    )

    assert report["physical"] == 10
    assert report["reserved"] == 3
    assert report["available"] == 7


def test_inventory_report_returns_expired_stock():
    service = create_service()
    inventory = create_inventory()

    inventory.add_batch(
        create_batch(
            batch_id="BATCH-001",
            quantity=10,
            expiry_date=date(2026, 9, 1),
        )
    )

    report = service.get_inventory_report(
        inventory=inventory,
        sku="LAPTOP-01",
        reference_date=date(2026, 9, 24),
    )

    assert report["expired"] == 10


def test_inventory_report_returns_quarantine_stock():
    service = create_service()

    inventory = create_inventory(
        warehouse_id="WH-Q",
        warehouse_type=WarehouseType.SCRAP_QUARANTINE,
    )

    inventory.add_batch(
        create_batch(
            batch_id="BATCH-001",
            quantity=8,
        )
    )

    report = service.get_inventory_report(
        inventory=inventory,
        sku="LAPTOP-01",
    )

    assert report["quarantine"] == 8


def test_inventory_report_detects_low_stock():
    service = create_service()
    inventory = create_inventory()

    inventory.add_batch(
        create_batch(
            batch_id="BATCH-001",
            quantity=5,
        )
    )

    report = service.get_inventory_report(
        inventory=inventory,
        sku="LAPTOP-01",
        low_stock_threshold=10,
    )

    assert report["available"] == 5
    assert report["low_stock_threshold"] == 10
    assert report["low_stock"] is True


def test_inventory_report_is_not_low_stock_above_threshold():
    service = create_service()
    inventory = create_inventory()

    inventory.add_batch(
        create_batch(
            batch_id="BATCH-001",
            quantity=15,
        )
    )

    report = service.get_inventory_report(
        inventory=inventory,
        sku="LAPTOP-01",
        low_stock_threshold=10,
    )

    assert report["low_stock"] is False


def test_inventory_report_returns_in_transit_stock():
    service = create_service()
    inventory = create_inventory()

    transaction = InventoryTransaction(
        timestamp=datetime(2026, 9, 24, 10, 0, 0),
        warehouse=inventory.warehouse,
        sku="LAPTOP-01",
        quantity=-5,
        transaction_type=InventoryTransactionType.TRANSFER_OUT,
        reference_id="TR-001",
    )

    service.ledger.record(transaction)

    report = service.get_inventory_report(
        inventory=inventory,
        sku="LAPTOP-01",
    )

    assert report["in_transit"] == 5


def test_received_transfer_is_not_counted_as_in_transit():
    service = create_service()
    source_inventory = create_inventory("WH-001")
    destination_inventory = create_inventory("WH-002")

    service.ledger.record(
        InventoryTransaction(
            timestamp=datetime(2026, 9, 24, 10, 0, 0),
            warehouse=source_inventory.warehouse,
            sku="LAPTOP-01",
            quantity=-5,
            transaction_type=InventoryTransactionType.TRANSFER_OUT,
            reference_id="TR-001",
        )
    )

    service.ledger.record(
        InventoryTransaction(
            timestamp=datetime(2026, 9, 24, 11, 0, 0),
            warehouse=destination_inventory.warehouse,
            sku="LAPTOP-01",
            quantity=5,
            transaction_type=InventoryTransactionType.TRANSFER_IN,
            reference_id="TR-001",
        )
    )

    report = service.get_inventory_report(
        inventory=source_inventory,
        sku="LAPTOP-01",
    )

    assert report["in_transit"] == 0


def test_inventory_report_for_all_warehouses():
    service = create_service()

    inventory_one = create_inventory("WH-001")
    inventory_two = create_inventory("WH-002")

    inventory_one.add_batch(
        create_batch(
            batch_id="BATCH-001",
            quantity=10,
        )
    )

    inventory_two.add_batch(
        create_batch(
            batch_id="BATCH-002",
            quantity=20,
        )
    )

    reports = service.get_inventory_report_for_all_warehouses(
        inventories=[
            inventory_one,
            inventory_two,
        ],
        sku="LAPTOP-01",
    )

    assert len(reports) == 2
    assert reports[0]["physical"] == 10
    assert reports[1]["physical"] == 20


def test_inventory_report_rejects_negative_threshold():
    service = create_service()
    inventory = create_inventory()

    with pytest.raises(ValueError):
        service.get_inventory_report(
            inventory=inventory,
            sku="LAPTOP-01",
            low_stock_threshold=-1,
        )