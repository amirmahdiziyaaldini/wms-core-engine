from datetime import datetime
from decimal import Decimal

import pytest

from app.domain.enums.order_status import OrderStatus
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem


def create_order_item(
    item_id: str = "ITEM-001",
    sku: str = "SKU-001",
    quantity: int = 2,
) -> OrderItem:
    return OrderItem(
        item_id=item_id,
        sku=sku,
        quantity=quantity,
    )


def test_order_stores_customer_id():
    order = Order(
        order_id="ORD-001",
        customer_id="CUS-001",
    )

    assert order.customer_id == "CUS-001"


def test_order_generates_created_at():
    order = Order(
        order_id="ORD-001",
    )

    assert isinstance(
        order.created_at,
        datetime,
    )


def test_order_accepts_created_at_snapshot():
    created_at = datetime(
        2026,
        9,
        25,
        12,
        30,
    )

    order = Order(
        order_id="ORD-001",
        created_at=created_at,
    )

    assert order.created_at == created_at


def test_order_initializes_lifecycle_timestamps_as_none():
    order = Order(
        order_id="ORD-001",
    )

    assert order.reserved_at is None
    assert order.paid_at is None
    assert order.shipped_at is None
    assert order.completed_at is None


def test_order_item_stores_product_name_snapshot():
    item = OrderItem(
        item_id="ITEM-001",
        sku="SKU-001",
        quantity=2,
        product_name="Python Book",
    )

    assert item.product_name == "Python Book"


def test_order_item_price_snapshot_calculates_line_total():
    item = OrderItem(
        item_id="ITEM-001",
        sku="SKU-001",
        quantity=3,
        product_name="Python Book",
        unit_price=Decimal("100"),
        discount=Decimal("20"),
    )

    assert item.unit_price == Decimal("100")
    assert item.discount == Decimal("20")
    assert item.line_total == Decimal("280")


def test_order_item_set_price_snapshot_updates_snapshot():
    item = create_order_item(
        quantity=3,
    )

    item.set_price_snapshot(
        unit_price=Decimal("150"),
        product_name="Advanced Python",
        discount=Decimal("50"),
    )

    assert item.unit_price == Decimal("150")
    assert item.product_name == "Advanced Python"
    assert item.discount == Decimal("50")
    assert item.line_total == Decimal("400")


def test_order_total_amount_is_sum_of_line_totals():
    order = Order(
        order_id="ORD-001",
    )

    item_one = OrderItem(
        item_id="ITEM-001",
        sku="SKU-001",
        quantity=2,
        unit_price=Decimal("100"),
        discount=Decimal("10"),
    )

    item_two = OrderItem(
        item_id="ITEM-002",
        sku="SKU-002",
        quantity=3,
        unit_price=Decimal("50"),
        discount=Decimal("20"),
    )

    order.add_item(item_one)
    order.add_item(item_two)

    assert item_one.line_total == Decimal("190")
    assert item_two.line_total == Decimal("130")
    assert order.total_amount == Decimal("320")


def test_order_total_is_not_manually_assignable():
    order = Order(
        order_id="ORD-001",
    )

    with pytest.raises(
        AttributeError,
    ):
        order.total_amount = Decimal("999")


def test_order_total_requires_priced_items():
    order = Order(
        order_id="ORD-001",
    )

    order.add_item(
        create_order_item()
    )

    with pytest.raises(
        ValueError,
        match="Order total cannot be calculated",
    ):
        order.calculate_total()


def test_order_item_quantity_must_be_positive():
    with pytest.raises(ValueError):
        OrderItem(
            item_id="ITEM-001",
            sku="SKU-001",
            quantity=0,
        )

    with pytest.raises(ValueError):
        OrderItem(
            item_id="ITEM-001",
            sku="SKU-001",
            quantity=-1,
        )


def test_order_item_boolean_quantity_is_rejected():
    with pytest.raises(ValueError):
        OrderItem(
            item_id="ITEM-001",
            sku="SKU-001",
            quantity=True,
        )

    with pytest.raises(ValueError):
        OrderItem(
            item_id="ITEM-001",
            sku="SKU-001",
            quantity=False,
        )


def test_order_item_negative_unit_price_is_rejected():
    with pytest.raises(ValueError):
        OrderItem(
            item_id="ITEM-001",
            sku="SKU-001",
            quantity=1,
            unit_price=Decimal("-1"),
        )


def test_order_item_negative_discount_is_rejected():
    with pytest.raises(ValueError):
        OrderItem(
            item_id="ITEM-001",
            sku="SKU-001",
            quantity=1,
            discount=Decimal("-1"),
        )


def test_order_item_discount_cannot_exceed_gross_total():
    with pytest.raises(ValueError):
        OrderItem(
            item_id="ITEM-001",
            sku="SKU-001",
            quantity=2,
            unit_price=Decimal("100"),
            discount=Decimal("201"),
        )


def test_order_rejects_invalid_customer_id():
    with pytest.raises(ValueError):
        Order(
            order_id="ORD-001",
            customer_id="",
        )

    with pytest.raises(ValueError):
        Order(
            order_id="ORD-001",
            customer_id=123,
        )


def test_order_rejects_invalid_created_at():
    with pytest.raises(ValueError):
        Order(
            order_id="ORD-001",
            created_at="2026-09-25",
        )


def test_order_preserves_status():
    order = Order(
        order_id="ORD-001",
        status=OrderStatus.PAID,
    )

    assert order.status == OrderStatus.PAID


def test_order_get_total_returns_calculated_total():
    order = Order(
        order_id="ORD-001",
    )

    order.add_item(
        OrderItem(
            item_id="ITEM-001",
            sku="SKU-001",
            quantity=2,
            unit_price=Decimal("100"),
            discount=Decimal("10"),
        )
    )

    assert order.get_total() == Decimal("190")


def test_product_name_snapshot_is_independent_from_external_value():
    product_name = "Python Fundamentals"

    item = OrderItem(
        item_id="ITEM-001",
        sku="SKU-001",
        quantity=1,
        product_name=product_name,
        unit_price=Decimal("100"),
    )

    product_name = "Changed Product"

    assert item.product_name == "Python Fundamentals"