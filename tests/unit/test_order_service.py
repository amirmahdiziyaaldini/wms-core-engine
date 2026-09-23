from decimal import Decimal

import pytest

from app.domain.enums.order_status import OrderStatus
from app.domain.enums.warehouse_type import WarehouseType
from app.domain.models.base_product import BaseProduct
from app.domain.models.batch import Batch
from app.domain.models.inventory import Inventory
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.domain.models.warehouse import Warehouse
from app.services.order_service import OrderService


def create_inventory(
    stock_laptop: int = 10,
    stock_mouse: int = 10,
):
    warehouse = Warehouse(
        warehouse_id="WH-001",
        name="Main Warehouse",
        location="Tehran",
        warehouse_type=WarehouseType.CENTRAL,
    )

    laptop = BaseProduct(
        sku="LAPTOP-01",
        name="Laptop",
        barcode="123456789",
        category="Electronics",
        base_price=Decimal("500000"),
    )

    mouse = BaseProduct(
        sku="MOUSE-01",
        name="Mouse",
        barcode="987654321",
        category="Electronics",
        base_price=Decimal("50000"),
    )

    inventory = Inventory(warehouse)

    inventory.add_batch(
        Batch(
            batch_id="BATCH-LAPTOP",
            product=laptop,
            quantity=stock_laptop,
        )
    )

    inventory.add_batch(
        Batch(
            batch_id="BATCH-MOUSE",
            product=mouse,
            quantity=stock_mouse,
        )
    )

    return inventory


def create_order():
    order = Order(order_id="ORD-001")

    order.add_item(
        OrderItem(
            item_id="ITEM-001",
            sku="LAPTOP-01",
            quantity=3,
        )
    )

    order.add_item(
        OrderItem(
            item_id="ITEM-002",
            sku="MOUSE-01",
            quantity=2,
        )
    )

    return order


def test_reserve_order_with_one_item():
    inventory = create_inventory()

    order = Order(order_id="ORD-001")

    order.add_item(
        OrderItem(
            item_id="ITEM-001",
            sku="LAPTOP-01",
            quantity=3,
        )
    )

    service = OrderService()

    reservations = service.reserve_order(
        order=order,
        inventory=inventory,
    )

    assert len(reservations) == 1

    reservation = reservations[0]

    assert reservation.order_id == "ORD-001"
    assert reservation.order_item_id == "ITEM-001"
    assert reservation.sku == "LAPTOP-01"
    assert reservation.quantity == 3

    assert inventory.get_reserved_stock("LAPTOP-01") == 3
    assert inventory.get_available_stock("LAPTOP-01") == 7


def test_reserve_order_with_multiple_items():
    inventory = create_inventory()
    order = create_order()

    service = OrderService()

    reservations = service.reserve_order(
        order=order,
        inventory=inventory,
    )

    assert len(reservations) == 2

    assert inventory.get_reserved_stock("LAPTOP-01") == 3
    assert inventory.get_reserved_stock("MOUSE-01") == 2

    assert inventory.get_available_stock("LAPTOP-01") == 7
    assert inventory.get_available_stock("MOUSE-01") == 8


def test_reservation_changes_order_status_to_reserved():
    inventory = create_inventory()
    order = create_order()

    service = OrderService()

    service.reserve_order(
        order=order,
        inventory=inventory,
    )

    assert order.status == OrderStatus.RESERVED


def test_reservation_fails_when_stock_is_insufficient():
    inventory = create_inventory(stock_laptop=2)

    order = Order(order_id="ORD-001")

    order.add_item(
        OrderItem(
            item_id="ITEM-001",
            sku="LAPTOP-01",
            quantity=3,
        )
    )

    service = OrderService()

    with pytest.raises(ValueError):
        service.reserve_order(
            order=order,
            inventory=inventory,
        )

    assert inventory.get_reserved_stock("LAPTOP-01") == 0


def test_failed_multi_item_reservation_is_atomic():
    inventory = create_inventory(
        stock_laptop=10,
        stock_mouse=1,
    )

    order = create_order()

    service = OrderService()

    with pytest.raises(ValueError):
        service.reserve_order(
            order=order,
            inventory=inventory,
        )

    assert inventory.get_reserved_stock("LAPTOP-01") == 0
    assert inventory.get_reserved_stock("MOUSE-01") == 0

    assert inventory.get_available_stock("LAPTOP-01") == 10
    assert inventory.get_available_stock("MOUSE-01") == 1

    assert order.status == OrderStatus.CREATED


def test_duplicate_order_item_reservation_is_rejected():
    inventory = create_inventory()

    order = Order(order_id="ORD-001")

    order.add_item(
        OrderItem(
            item_id="ITEM-001",
            sku="LAPTOP-01",
            quantity=3,
        )
    )

    service = OrderService()

    service.reserve_order(
        order=order,
        inventory=inventory,
    )

    with pytest.raises(ValueError):
        service.reserve_order(
            order=order,
            inventory=inventory,
        )

    assert inventory.get_reserved_stock("LAPTOP-01") == 3


def test_order_without_items_cannot_be_reserved():
    inventory = create_inventory()

    order = Order(order_id="ORD-001")

    service = OrderService()

    with pytest.raises(ValueError):
        service.reserve_order(
            order=order,
            inventory=inventory,
        )


def test_release_order_reservations():
    inventory = create_inventory()
    order = create_order()

    service = OrderService()

    service.reserve_order(
        order=order,
        inventory=inventory,
    )

    assert inventory.get_reserved_stock("LAPTOP-01") == 3
    assert inventory.get_reserved_stock("MOUSE-01") == 2

    service.release_order_reservations(
        order=order,
        inventory=inventory,
    )

    assert inventory.get_reserved_stock("LAPTOP-01") == 0
    assert inventory.get_reserved_stock("MOUSE-01") == 0

    assert inventory.get_available_stock("LAPTOP-01") == 10
    assert inventory.get_available_stock("MOUSE-01") == 10


def test_release_only_removes_reservations_of_same_order():
    inventory = create_inventory()

    order_1 = Order(order_id="ORD-001")
    order_1.add_item(
        OrderItem(
            item_id="ITEM-001",
            sku="LAPTOP-01",
            quantity=3,
        )
    )

    order_2 = Order(order_id="ORD-002")
    order_2.add_item(
        OrderItem(
            item_id="ITEM-002",
            sku="LAPTOP-01",
            quantity=2,
        )
    )

    service = OrderService()

    service.reserve_order(
        order=order_1,
        inventory=inventory,
    )

    service.reserve_order(
        order=order_2,
        inventory=inventory,
    )

    assert inventory.get_reserved_stock("LAPTOP-01") == 5

    service.release_order_reservations(
        order=order_1,
        inventory=inventory,
    )

    assert inventory.get_reserved_stock("LAPTOP-01") == 2
    assert inventory.get_available_stock("LAPTOP-01") == 8


def test_failed_commit_rolls_back_new_reservations():
    inventory = create_inventory()

    order = create_order()

    service = OrderService()

    original_reserve_reservation = inventory.reserve_reservation

    call_count = 0

    def failing_reserve_reservation(reservation):
        nonlocal call_count

        call_count += 1

        if call_count == 2:
            raise ValueError("Simulated commit failure")

        original_reserve_reservation(reservation)

    inventory.reserve_reservation = failing_reserve_reservation

    with pytest.raises(ValueError):
        service.reserve_order(
            order=order,
            inventory=inventory,
        )

    assert inventory.get_reserved_stock("LAPTOP-01") == 0
    assert inventory.get_reserved_stock("MOUSE-01") == 0

    assert inventory.get_available_stock("LAPTOP-01") == 10
    assert inventory.get_available_stock("MOUSE-01") == 10

    assert order.status == OrderStatus.CREATED