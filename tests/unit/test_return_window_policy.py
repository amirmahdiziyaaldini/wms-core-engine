from datetime import datetime
from decimal import Decimal

import pytest

from app.domain.enums.order_status import OrderStatus
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.services.return_window_policy import ReturnWindowPolicy


def create_delivered_order(delivered_at: datetime) -> Order:
    order = Order(
        order_id="ORD-001",
        customer_id="CUS-001",
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

    order._set_status(
        OrderStatus.SHIPPED,
        delivered_at,
    )

    order._set_status(
        OrderStatus.DELIVERED,
        delivered_at,
    )

    return order


def test_return_is_allowed_within_seven_days():
    delivered_at = datetime(2026, 9, 1, 10, 0)
    now = datetime(2026, 9, 5, 10, 0)

    order = create_delivered_order(delivered_at)

    policy = ReturnWindowPolicy(
        return_window_days=7,
        now_provider=lambda: now,
    )

    policy.validate(order)

    assert policy.is_within_window(order) is True


def test_return_is_allowed_exactly_on_seventh_day():
    delivered_at = datetime(2026, 9, 1, 10, 0)
    now = datetime(2026, 9, 8, 10, 0)

    order = create_delivered_order(delivered_at)

    policy = ReturnWindowPolicy(
        return_window_days=7,
        now_provider=lambda: now,
    )

    policy.validate(order)

    assert policy.is_within_window(order) is True


def test_return_is_rejected_after_seventh_day():
    delivered_at = datetime(2026, 9, 1, 10, 0)
    now = datetime(2026, 9, 8, 10, 0, 1)

    order = create_delivered_order(delivered_at)

    policy = ReturnWindowPolicy(
        return_window_days=7,
        now_provider=lambda: now,
    )

    with pytest.raises(
        ValueError,
        match="Return window has expired",
    ):
        policy.validate(order)

    assert policy.is_within_window(order) is False


def test_return_window_days_is_configurable():
    delivered_at = datetime(2026, 9, 1, 10, 0)
    now = datetime(2026, 9, 11, 10, 0)

    order = create_delivered_order(delivered_at)

    policy = ReturnWindowPolicy(
        return_window_days=10,
        now_provider=lambda: now,
    )

    policy.validate(order)

    assert policy.is_within_window(order) is True


def test_non_delivered_order_is_rejected():
    order = Order(
        order_id="ORD-001",
        customer_id="CUS-001",
    )

    policy = ReturnWindowPolicy(
        return_window_days=7,
        now_provider=lambda: datetime(2026, 9, 8, 10, 0),
    )

    with pytest.raises(
        ValueError,
        match="Only delivered orders can be returned",
    ):
        policy.validate(order)

    assert policy.is_within_window(order) is False


def test_delivered_order_without_delivered_at_is_rejected():
    order = Order(
        order_id="ORD-001",
        customer_id="CUS-001",
    )

    order._set_status(
        OrderStatus.SHIPPED,
        datetime(2026, 9, 1, 10, 0),
    )

    order._status = OrderStatus.DELIVERED
    order.delivered_at = None

    policy = ReturnWindowPolicy(
        return_window_days=7,
        now_provider=lambda: datetime(2026, 9, 5, 10, 0),
    )

    with pytest.raises(
        ValueError,
        match="Delivered order must have delivered_at",
    ):
        policy.validate(order)

    assert policy.is_within_window(order) is False


def test_now_provider_must_return_datetime():
    delivered_at = datetime(2026, 9, 1, 10, 0)
    order = create_delivered_order(delivered_at)

    policy = ReturnWindowPolicy(
        return_window_days=7,
        now_provider=lambda: "2026-09-05",
    )

    with pytest.raises(
        ValueError,
        match="Now provider must return a datetime",
    ):
        policy.validate(order)


def test_current_time_before_delivery_is_rejected():
    delivered_at = datetime(2026, 9, 10, 10, 0)
    now = datetime(2026, 9, 9, 10, 0)

    order = create_delivered_order(delivered_at)

    policy = ReturnWindowPolicy(
        return_window_days=7,
        now_provider=lambda: now,
    )

    with pytest.raises(
        ValueError,
        match="Current time cannot be before delivered_at",
    ):
        policy.validate(order)