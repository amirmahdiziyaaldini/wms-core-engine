from datetime import datetime
from decimal import Decimal

import pytest

from app.domain.enums.order_status import OrderStatus
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.services.return_eligibility_service import ReturnEligibilityService


def create_order():
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

    return order


def set_status(order, status):
    order._set_status(
        status,
        datetime(2026, 9, 26, 10, 0),
    )


def test_delivered_order_is_eligible_for_rma():
    service = ReturnEligibilityService()
    order = create_order()

    set_status(
        order,
        OrderStatus.SHIPPED,
    )

    set_status(
        order,
        OrderStatus.DELIVERED,
    )

    service.validate_order_eligibility(order)

    assert service.is_eligible(order) is True


def test_created_order_is_not_eligible_for_rma():
    service = ReturnEligibilityService()
    order = create_order()

    with pytest.raises(
        ValueError,
        match="Created orders are not eligible for RMA",
    ):
        service.validate_order_eligibility(order)

    assert service.is_eligible(order) is False


def test_reserved_order_is_not_eligible_for_rma():
    service = ReturnEligibilityService()
    order = create_order()

    set_status(
        order,
        OrderStatus.RESERVED,
    )

    with pytest.raises(
        ValueError,
        match="Reserved orders are not eligible for RMA",
    ):
        service.validate_order_eligibility(order)

    assert service.is_eligible(order) is False


def test_paid_order_uses_cancellation_or_refund_instead_of_rma():
    service = ReturnEligibilityService()
    order = create_order()

    set_status(
        order,
        OrderStatus.PAID,
    )

    with pytest.raises(
        ValueError,
        match="Paid orders that have not been delivered must use cancellation or refund instead of RMA",
    ):
        service.validate_order_eligibility(order)

    assert service.is_eligible(order) is False


def test_shipped_order_is_not_eligible_for_rma_before_delivery():
    service = ReturnEligibilityService()
    order = create_order()

    set_status(
        order,
        OrderStatus.SHIPPED,
    )

    with pytest.raises(
        ValueError,
        match="Shipped orders are not eligible for RMA until delivery",
    ):
        service.validate_order_eligibility(order)

    assert service.is_eligible(order) is False


def test_cancelled_order_is_not_eligible_for_rma():
    service = ReturnEligibilityService()
    order = create_order()

    set_status(
        order,
        OrderStatus.CANCELLED,
    )

    with pytest.raises(
        ValueError,
        match="Cancelled orders are not eligible for RMA",
    ):
        service.validate_order_eligibility(order)

    assert service.is_eligible(order) is False


def test_invalid_order_is_rejected():
    service = ReturnEligibilityService()

    with pytest.raises(
        ValueError,
        match="Order must be an Order",
    ):
        service.validate_order_eligibility("ORD-001")

    with pytest.raises(
        ValueError,
        match="Order must be an Order",
    ):
        service.is_eligible("ORD-001")