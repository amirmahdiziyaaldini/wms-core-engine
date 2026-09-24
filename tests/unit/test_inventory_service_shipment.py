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
from app.domain.models.reservation import Reservation
from app.domain.models.warehouse import Warehouse
from app.services.inventory_service import InventoryService


def create_product(sku="LAPTOP-01"):
    return BaseProduct(
        sku=sku,
        name="Laptop",
        barcode="123456789",
        category="Electronics",
        base_price=Decimal("500000"),
    )


def create_warehouse():
    return Warehouse(
        warehouse_id="WH-001",
        name="Central Warehouse",
        location="Tehran",
        warehouse_type=WarehouseType.CENTRAL,
    )


def create_batch(
    quantity=10,
    sku="LAPTOP-01",
    batch_id="BATCH-001",
    serial_numbers=None,
):
    return Batch(
        batch_id=batch_id,
        product=create_product(sku),
        quantity=quantity,
        entry_date=date(2026, 9, 1),
        serial_numbers=serial_numbers,
    )


def create_reservation(
    reservation_id="RES-001",
    order_id="ORD-001",
    sku="LAPTOP-01",
    quantity=4,
    batch_allocations=None,
):
    return Reservation(
        reservation_id=reservation_id,
        order_id=order_id,
        order_item_id="ITEM-001",
        sku=sku,
        quantity=quantity,
        batch_allocations=batch_allocations,
    )


def test_consume_reservation_reduces_batch_quantity():
    inventory = Inventory(create_warehouse())
    ledger = InventoryLedger()
    service = InventoryService(ledger)

    batch = create_batch(quantity=10)

    inventory.add_batch(batch)

    reservation = create_reservation(
        quantity=4,
        batch_allocations={
            "BATCH-001": 4,
        },
    )

    inventory.reserve_reservation(reservation)

    service.consume_reservation(
        inventory=inventory,
        reservation_id="RES-001",
        timestamp=datetime(2026, 9, 24, 10, 0),
    )

    assert batch.quantity == 6


def test_consume_reservation_reduces_physical_stock():
    inventory = Inventory(create_warehouse())
    ledger = InventoryLedger()
    service = InventoryService(ledger)

    inventory.add_batch(
        create_batch(quantity=10)
    )

    reservation = create_reservation(
        quantity=4,
        batch_allocations={
            "BATCH-001": 4,
        },
    )

    inventory.reserve_reservation(reservation)

    service.consume_reservation(
        inventory=inventory,
        reservation_id="RES-001",
        timestamp=datetime(2026, 9, 24, 10, 0),
    )

    assert inventory.get_physical_stock(
        "LAPTOP-01"
    ) == 6


def test_consume_reservation_releases_reserved_stock():
    inventory = Inventory(create_warehouse())
    ledger = InventoryLedger()
    service = InventoryService(ledger)

    inventory.add_batch(
        create_batch(quantity=10)
    )

    reservation = create_reservation(
        quantity=4,
        batch_allocations={
            "BATCH-001": 4,
        },
    )

    inventory.reserve_reservation(reservation)

    assert inventory.get_reserved_stock(
        "LAPTOP-01"
    ) == 4

    service.consume_reservation(
        inventory=inventory,
        reservation_id="RES-001",
        timestamp=datetime(2026, 9, 24, 10, 0),
    )

    assert inventory.get_reserved_stock(
        "LAPTOP-01"
    ) == 0


def test_consume_reservation_records_ship_transaction():
    inventory = Inventory(create_warehouse())
    ledger = InventoryLedger()
    service = InventoryService(ledger)

    inventory.add_batch(
        create_batch(quantity=10)
    )

    reservation = create_reservation(
        quantity=4,
        batch_allocations={
            "BATCH-001": 4,
        },
    )

    inventory.reserve_reservation(reservation)

    service.consume_reservation(
        inventory=inventory,
        reservation_id="RES-001",
        timestamp=datetime(2026, 9, 24, 10, 0),
    )

    assert len(ledger.transactions) == 1

    transaction = ledger.transactions[0]

    assert transaction.transaction_type == (
        InventoryTransactionType.SHIP
    )
    assert transaction.quantity == -4
    assert transaction.sku == "LAPTOP-01"
    assert transaction.batch_id == "BATCH-001"
    assert transaction.reference_id == "ORD-001"


def test_consume_reservation_uses_exact_batch_allocations():
    inventory = Inventory(create_warehouse())
    ledger = InventoryLedger()
    service = InventoryService(ledger)

    batch_1 = create_batch(
        quantity=10,
        batch_id="BATCH-001",
    )

    batch_2 = create_batch(
        quantity=20,
        batch_id="BATCH-002",
    )

    inventory.add_batch(batch_1)
    inventory.add_batch(batch_2)

    reservation = create_reservation(
        quantity=7,
        batch_allocations={
            "BATCH-001": 3,
            "BATCH-002": 4,
        },
    )

    inventory.reserve_reservation(reservation)

    service.consume_reservation(
        inventory=inventory,
        reservation_id="RES-001",
        timestamp=datetime(2026, 9, 24, 10, 0),
    )

    assert batch_1.quantity == 7
    assert batch_2.quantity == 16


def test_consume_reservation_rejects_missing_batch():
    inventory = Inventory(create_warehouse())
    ledger = InventoryLedger()
    service = InventoryService(ledger)

    inventory.add_batch(
        create_batch(quantity=10)
    )

    reservation = create_reservation(
        quantity=4,
        batch_allocations={
            "BATCH-999": 4,
        },
    )

    inventory.reserve_reservation(reservation)

    with pytest.raises(ValueError):
        service.consume_reservation(
            inventory=inventory,
            reservation_id="RES-001",
            timestamp=datetime(2026, 9, 24, 10, 0),
        )

    assert inventory.get_physical_stock(
        "LAPTOP-01"
    ) == 10


def test_consume_reservation_rejects_mismatched_allocation_quantity():
    inventory = Inventory(create_warehouse())
    ledger = InventoryLedger()
    service = InventoryService(ledger)

    inventory.add_batch(
        create_batch(quantity=10)
    )

    reservation = create_reservation(
        quantity=4,
        batch_allocations={
            "BATCH-001": 3,
        },
    )

    inventory.reserve_reservation(reservation)

    with pytest.raises(ValueError):
        service.consume_reservation(
            inventory=inventory,
            reservation_id="RES-001",
            timestamp=datetime(2026, 9, 24, 10, 0),
        )


def test_consume_serialized_reservation_records_serial_numbers():
    inventory = Inventory(create_warehouse())
    ledger = InventoryLedger()
    service = InventoryService(ledger)

    inventory.add_batch(
        create_batch(
            quantity=3,
            serial_numbers=[
                "SER-001",
                "SER-002",
                "SER-003",
            ],
        )
    )

    reservation = create_reservation(
        quantity=2,
        batch_allocations={
            "BATCH-001": 2,
        },
    )

    inventory.reserve_reservation(reservation)

    shipped_serial_numbers = service.consume_reservation(
        inventory=inventory,
        reservation_id="RES-001",
        timestamp=datetime(2026, 9, 24, 10, 0),
    )

    assert shipped_serial_numbers == [
        "SER-001",
        "SER-002",
    ]

    assert inventory.batches[0].serial_numbers == [
        "SER-003"
    ]

    assert ledger.transactions[0].serial_numbers == [
        "SER-001",
        "SER-002",
    ]