from datetime import date
from decimal import Decimal

from app.domain.enums.warehouse_type import WarehouseType
from app.domain.models.base_product import BaseProduct
from app.domain.models.batch import Batch
from app.domain.models.inventory import Inventory
from app.domain.models.inventory_ledger import InventoryLedger
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.domain.models.warehouse import Warehouse
from app.services.inventory_service import InventoryService
from app.services.order_service import OrderService
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


def create_order(quantity=5):
    order = Order("ORD-1001")

    order.add_item(
        OrderItem(
            item_id="ITEM-001",
            sku="LAPTOP-01",
            quantity=quantity,
        )
    )

    return order


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


def create_order_service(strategy=None):
    if strategy is None:
        inventory_service = InventoryService(
            InventoryLedger()
        )
    else:
        inventory_service = InventoryService(
            InventoryLedger(),
            strategy,
        )

    return OrderService(inventory_service)


def test_order_reservation_contains_fifo_batch_allocations():
    inventory = create_inventory()
    order = create_order(quantity=5)

    service = create_order_service(
        FIFOStockAllocationStrategy()
    )

    reservations = service.reserve_order(
        order=order,
        inventory=inventory,
    )

    assert len(reservations) == 1

    reservation = reservations[0]

    assert reservation.batch_allocations == {
        "B-001": 5,
    }


def test_order_reservation_contains_lifo_batch_allocations():
    inventory = create_inventory()
    order = create_order(quantity=5)

    service = create_order_service(
        LIFOStockAllocationStrategy()
    )

    reservations = service.reserve_order(
        order=order,
        inventory=inventory,
    )

    reservation = reservations[0]

    assert reservation.batch_allocations == {
        "B-002": 5,
    }


def test_order_reservation_can_use_multiple_batches():
    inventory = create_inventory()
    order = create_order(quantity=15)

    service = create_order_service(
        FIFOStockAllocationStrategy()
    )

    reservations = service.reserve_order(
        order=order,
        inventory=inventory,
    )

    reservation = reservations[0]

    assert reservation.batch_allocations == {
        "B-001": 10,
        "B-002": 5,
    }


def test_reservation_does_not_change_physical_stock():
    inventory = create_inventory()
    order = create_order(quantity=7)

    service = create_order_service()

    physical_before = inventory.get_physical_stock(
        "LAPTOP-01"
    )

    service.reserve_order(
        order=order,
        inventory=inventory,
    )

    physical_after = inventory.get_physical_stock(
        "LAPTOP-01"
    )

    assert physical_before == 20
    assert physical_after == 20


def test_reservation_reduces_available_stock():
    inventory = create_inventory()
    order = create_order(quantity=7)

    service = create_order_service()

    service.reserve_order(
        order=order,
        inventory=inventory,
    )

    assert (
        inventory.get_reserved_stock("LAPTOP-01")
        == 7
    )

    assert (
        inventory.get_available_stock("LAPTOP-01")
        == 13
    )


def test_expired_batch_is_not_allocated():
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

    order = create_order(quantity=5)

    service = create_order_service(
        FIFOStockAllocationStrategy()
    )

    reservations = service.reserve_order(
        order=order,
        inventory=inventory,
        reference_date=date(2026, 9, 20),
    )

    reservation = reservations[0]

    assert reservation.batch_allocations == {
        "B-002": 5,
    }