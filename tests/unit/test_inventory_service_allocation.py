from datetime import date
from decimal import Decimal

from app.domain.enums.warehouse_type import WarehouseType
from app.domain.models.base_product import BaseProduct
from app.domain.models.batch import Batch
from app.domain.models.inventory import Inventory
from app.domain.models.inventory_ledger import InventoryLedger
from app.domain.models.warehouse import Warehouse
from app.services.inventory_service import InventoryService
from app.strategies.fifo_stock_allocation_strategy import (
    FIFOStockAllocationStrategy,
)
from app.strategies.lifo_stock_allocation_strategy import (
    LIFOStockAllocationStrategy,
)


def create_warehouse():
    return Warehouse(
        warehouse_id="WH-001",
        name="Central Warehouse",
        location="Frankfurt",
        warehouse_type=WarehouseType.CENTRAL,
    )


def create_product(sku="LAPTOP-01"):
    return BaseProduct(
        sku=sku,
        name="Laptop",
        barcode="123456789",
        category="Electronics",
        base_price=Decimal("1000"),
    )


def create_batch(
    batch_id,
    quantity,
    entry_date,
    sku="LAPTOP-01",
    expiry_date=None,
):
    return Batch(
        batch_id=batch_id,
        product=create_product(sku),
        quantity=quantity,
        entry_date=entry_date,
        expiry_date=expiry_date,
    )


def create_inventory():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(
            batch_id="B-001",
            quantity=10,
            entry_date=date(2026, 9, 1),
        )
    )

    inventory.add_batch(
        create_batch(
            batch_id="B-002",
            quantity=10,
            entry_date=date(2026, 9, 10),
        )
    )

    return inventory


def create_service(strategy=None):
    if strategy is None:
        return InventoryService(
            InventoryLedger()
        )

    return InventoryService(
        InventoryLedger(),
        strategy,
    )


def test_inventory_service_uses_fifo_strategy():
    inventory = create_inventory()

    service = create_service(
        FIFOStockAllocationStrategy()
    )

    result = service.allocate_stock(
        inventory=inventory,
        sku="LAPTOP-01",
        quantity=5,
    )

    assert result == {
        "B-001": 5,
    }


def test_inventory_service_uses_lifo_strategy():
    inventory = create_inventory()

    service = create_service(
        LIFOStockAllocationStrategy()
    )

    result = service.allocate_stock(
        inventory=inventory,
        sku="LAPTOP-01",
        quantity=5,
    )

    assert result == {
        "B-002": 5,
    }


def test_inventory_service_allocates_only_requested_sku():
    inventory = create_inventory()

    inventory.add_batch(
        create_batch(
            batch_id="B-003",
            quantity=10,
            entry_date=date(2026, 9, 2),
            sku="PHONE-01",
        )
    )

    service = create_service(
        FIFOStockAllocationStrategy()
    )

    result = service.allocate_stock(
        inventory=inventory,
        sku="LAPTOP-01",
        quantity=5,
    )

    assert result == {
        "B-001": 5,
    }


def test_inventory_service_uses_fifo_by_default():
    inventory = create_inventory()

    service = create_service()

    result = service.allocate_stock(
        inventory=inventory,
        sku="LAPTOP-01",
        quantity=5,
    )

    assert result == {
        "B-001": 5,
    }


def test_inventory_service_skips_expired_batches():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(
            batch_id="B-001",
            quantity=10,
            entry_date=date(2026, 9, 1),
            expiry_date=date(2026, 9, 10),
        )
    )

    inventory.add_batch(
        create_batch(
            batch_id="B-002",
            quantity=10,
            entry_date=date(2026, 9, 5),
            expiry_date=date(2026, 12, 1),
        )
    )

    service = create_service(
        FIFOStockAllocationStrategy()
    )

    result = service.allocate_stock(
        inventory=inventory,
        sku="LAPTOP-01",
        quantity=5,
        reference_date=date(2026, 9, 20),
    )

    assert result == {
        "B-002": 5,
    }