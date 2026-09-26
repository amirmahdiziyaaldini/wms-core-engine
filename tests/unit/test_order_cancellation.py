from datetime import date, datetime
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


def create_inventory():
    warehouse = Warehouse(
        warehouse_id="WH-001",
        name="Main Warehouse",
        location="Berlin",
        warehouse_type=WarehouseType.CENTRAL,
    )

    inventory = Inventory(
        warehouse=warehouse,
    )

    product = BaseProduct(
        sku="LAPTOP-01",
        name="Laptop",
        barcode="123456789",
        category="Electronics",
        base_price=Decimal("100"),
    )

    batch = Batch(
        batch_id="BATCH-001",
        product=product,
        quantity=10,
        entry_date=date(2026, 1, 1),
    )

    inventory.add_batch(batch)

    return inventory


def create_order(status=OrderStatus.CREATED):
    order = Order(
        order_id="ORD-001",
        customer_id="CUS-001",
        status=status,
    )

    order.add_item(
        OrderItem(
            item_id="ITEM-001",
            sku="LAPTOP-01",
            quantity=2,
            product_name="Laptop",
            unit_price=Decimal("100"),
        )
    )

    return order


def reserve_order(service, order, inventory):
    service.reserve_order(
        order=order,
        inventory=inventory,
    )


def test_cancel_created_order():
    service = OrderService()
    inventory = create_inventory()
    order = create_order()

    service.cancel_order(
        order=order,
        inventory=inventory,
    )

    assert order.status == OrderStatus.CANCELLED
    assert order.cancelled_at is not None


def test_cancel_reserved_order_releases_reservations():
    service = OrderService()
    inventory = create_inventory()
    order = create_order()

    reserve_order(service, order, inventory)

    assert order.status == OrderStatus.RESERVED
    assert inventory.get_available_stock("LAPTOP-01") == 8

    service.cancel_order(
        order=order,
        inventory=inventory,
    )

    assert order.status == OrderStatus.CANCELLED
    assert order.cancelled_at is not None
    assert inventory.get_available_stock("LAPTOP-01") == 10
    assert len(inventory.reservations) == 0


def test_cancel_paid_order_releases_reservations():
    service = OrderService()
    inventory = create_inventory()
    order = create_order()

    reserve_order(service, order, inventory)

    service.mark_as_paid(
        order=order,
        transaction_reference="TX-001",
        amount=Decimal("200"),
    )

    assert order.status == OrderStatus.PAID
    assert inventory.get_available_stock("LAPTOP-01") == 8

    service.cancel_order(
        order=order,
        inventory=inventory,
    )

    assert order.status == OrderStatus.CANCELLED
    assert order.cancelled_at is not None
    assert inventory.get_available_stock("LAPTOP-01") == 10
    assert len(inventory.reservations) == 0


def test_cancel_shipped_order_is_rejected():
    service = OrderService()
    inventory = create_inventory()
    order = create_order()

    order._set_status(
        OrderStatus.SHIPPED,
        datetime(2026, 1, 2),
    )

    with pytest.raises(
        ValueError,
        match="Shipped or delivered orders cannot be cancelled",
    ):
        service.cancel_order(
            order=order,
            inventory=inventory,
        )

    assert order.status == OrderStatus.SHIPPED


def test_cancel_delivered_order_is_rejected():
    service = OrderService()
    inventory = create_inventory()
    order = create_order()

    order._set_status(
        OrderStatus.DELIVERED,
        datetime(2026, 1, 3),
    )

    with pytest.raises(
        ValueError,
        match="Shipped or delivered orders cannot be cancelled",
    ):
        service.cancel_order(
            order=order,
            inventory=inventory,
        )

    assert order.status == OrderStatus.DELIVERED


def test_cancelled_order_cannot_be_cancelled_again():
    service = OrderService()
    inventory = create_inventory()
    order = create_order()

    service.cancel_order(
        order=order,
        inventory=inventory,
    )

    with pytest.raises(
        ValueError,
        match="Order is already cancelled",
    ):
        service.cancel_order(
            order=order,
            inventory=inventory,
        )

    assert order.status == OrderStatus.CANCELLED


def test_cancel_does_not_create_artificial_inventory():
    service = OrderService()
    inventory = create_inventory()
    order = create_order()

    initial_physical_stock = inventory.get_physical_stock("LAPTOP-01")
    initial_available_stock = inventory.get_available_stock("LAPTOP-01")

    service.cancel_order(
        order=order,
        inventory=inventory,
    )

    assert inventory.get_physical_stock("LAPTOP-01") == initial_physical_stock
    assert inventory.get_available_stock("LAPTOP-01") == initial_available_stock