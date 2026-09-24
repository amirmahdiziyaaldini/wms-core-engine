import pytest

from app.domain.enums.order_status import OrderStatus
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem


def create_order_item(
    item_id="ITEM-001",
    sku="LAPTOP-01",
    quantity=2,
):
    return OrderItem(
        item_id=item_id,
        sku=sku,
        quantity=quantity,
    )


def test_create_order():
    order = Order(
        order_id="ORD-001",
    )

    assert order.order_id == "ORD-001"
    assert order.status == OrderStatus.CREATED
    assert order.items == []


def test_create_order_with_status():
    order = Order(
        order_id="ORD-001",
        status=OrderStatus.PAID,
    )

    assert order.status == OrderStatus.PAID


def test_order_id_must_be_string():
    with pytest.raises(ValueError):
        Order(
            order_id=123,
        )


def test_order_id_cannot_be_empty():
    with pytest.raises(ValueError):
        Order(
            order_id="",
        )


def test_order_id_cannot_contain_only_whitespace():
    with pytest.raises(ValueError):
        Order(
            order_id="   ",
        )


def test_status_must_be_order_status():
    with pytest.raises(ValueError):
        Order(
            order_id="ORD-001",
            status="created",
        )


def test_add_order_item():
    order = Order(
        order_id="ORD-001",
    )

    item = create_order_item()

    order.add_item(item)

    assert order.items == [item]


def test_add_multiple_order_items():
    order = Order(
        order_id="ORD-001",
    )

    item_1 = create_order_item(
        item_id="ITEM-001",
        sku="LAPTOP-01",
    )

    item_2 = create_order_item(
        item_id="ITEM-002",
        sku="MOUSE-01",
        quantity=3,
    )

    order.add_item(item_1)
    order.add_item(item_2)

    assert order.items == [
        item_1,
        item_2,
    ]


def test_add_item_requires_order_item():
    order = Order(
        order_id="ORD-001",
    )

    with pytest.raises(ValueError):
        order.add_item("LAPTOP-01")


def test_duplicate_order_item_id_is_rejected():
    order = Order(
        order_id="ORD-001",
    )

    item_1 = create_order_item(
        item_id="ITEM-001",
        sku="LAPTOP-01",
    )

    item_2 = create_order_item(
        item_id="ITEM-001",
        sku="MOUSE-01",
    )

    order.add_item(item_1)

    with pytest.raises(ValueError):
        order.add_item(item_2)