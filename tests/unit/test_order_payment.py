from decimal import Decimal

import pytest

from app.domain.enums.order_status import OrderStatus
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.services.order_service import OrderService


def create_paid_ready_order(
    status: OrderStatus = OrderStatus.CREATED,
) -> Order:
    order = Order(
        order_id="ORD-001",
        customer_id="CUS-001",
        status=status,
    )

    order.add_item(
        OrderItem(
            item_id="ITEM-001",
            sku="SKU-001",
            quantity=2,
            product_name="Product",
            unit_price=Decimal("100"),
        )
    )

    return order


def test_mark_as_paid_changes_order_status():
    service = OrderService()

    order = create_paid_ready_order()

    transaction = service.mark_as_paid(
        order=order,
        transaction_reference="REF-001",
        amount=Decimal("200"),
    )

    assert order.status == OrderStatus.PAID
    assert transaction.order_id == "ORD-001"
    assert transaction.reference == "REF-001"
    assert transaction.amount == Decimal("200")


def test_mark_as_paid_creates_financial_transaction_log():
    service = OrderService()

    order = create_paid_ready_order()

    transaction = service.mark_as_paid(
        order=order,
        transaction_reference="REF-001",
        amount=Decimal("200"),
    )

    saved_transaction = (
        service.payment_transaction_repository.get(
            transaction.transaction_id
        )
    )

    assert saved_transaction is transaction


def test_mark_as_paid_allows_reserved_order():
    service = OrderService()

    order = create_paid_ready_order(
        status=OrderStatus.RESERVED,
    )

    service.mark_as_paid(
        order=order,
        transaction_reference="REF-001",
        amount=Decimal("200"),
    )

    assert order.status == OrderStatus.PAID


def test_mark_as_paid_rejects_invalid_order_status():
    service = OrderService()

    order = create_paid_ready_order(
        status=OrderStatus.SHIPPED,
    )

    with pytest.raises(
        ValueError,
        match="Order cannot be paid in its current state",
    ):
        service.mark_as_paid(
            order=order,
            transaction_reference="REF-001",
            amount=Decimal("200"),
        )


def test_mark_as_paid_rejects_second_payment():
    service = OrderService()

    order = create_paid_ready_order()

    service.mark_as_paid(
        order=order,
        transaction_reference="REF-001",
        amount=Decimal("200"),
    )

    with pytest.raises(
        ValueError,
        match="Order is already paid",
    ):
        service.mark_as_paid(
            order=order,
            transaction_reference="REF-002",
            amount=Decimal("200"),
        )


def test_mark_as_paid_rejects_wrong_amount():
    service = OrderService()

    order = create_paid_ready_order()

    with pytest.raises(
        ValueError,
        match="Payment amount must match order total",
    ):
        service.mark_as_paid(
            order=order,
            transaction_reference="REF-001",
            amount=Decimal("150"),
        )

    assert order.status == OrderStatus.CREATED
    assert (
        service.payment_transaction_repository.list_all()
        == []
    )


def test_mark_as_paid_rejects_duplicate_reference():
    service = OrderService()

    order_one = create_paid_ready_order()

    service.mark_as_paid(
        order=order_one,
        transaction_reference="REF-001",
        amount=Decimal("200"),
    )

    order_two = Order(
        order_id="ORD-002",
        customer_id="CUS-002",
    )

    order_two.add_item(
        OrderItem(
            item_id="ITEM-002",
            sku="SKU-002",
            quantity=1,
            product_name="Product",
            unit_price=Decimal("200"),
        )
    )

    with pytest.raises(
        ValueError,
        match="Payment reference already exists",
    ):
        service.mark_as_paid(
            order=order_two,
            transaction_reference="REF-001",
            amount=Decimal("200"),
        )

    assert order_two.status == OrderStatus.CREATED


def test_mark_as_paid_rejects_empty_reference():
    service = OrderService()

    order = create_paid_ready_order()

    with pytest.raises(
        ValueError,
        match="Payment reference cannot be empty",
    ):
        service.mark_as_paid(
            order=order,
            transaction_reference="",
            amount=Decimal("200"),
        )

    assert order.status == OrderStatus.CREATED