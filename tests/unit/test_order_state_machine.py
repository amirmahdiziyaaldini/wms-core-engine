from datetime import datetime

import pytest

from app.domain.enums.order_status import OrderStatus
from app.domain.models.order import Order
from app.domain.states.order_state_machine import OrderStateMachine


def test_created_can_transition_to_paid():
    order = Order("ORD-001")
    state_machine = OrderStateMachine()

    state_machine.transition(
        order,
        OrderStatus.PAID,
    )

    assert order.status == OrderStatus.PAID
    assert isinstance(order.paid_at, datetime)


def test_paid_can_transition_to_shipped():
    order = Order(
        "ORD-001",
        status=OrderStatus.PAID,
    )
    state_machine = OrderStateMachine()

    state_machine.transition(
        order,
        OrderStatus.SHIPPED,
    )

    assert order.status == OrderStatus.SHIPPED
    assert isinstance(order.shipped_at, datetime)


def test_shipped_can_transition_to_delivered():
    order = Order(
        "ORD-001",
        status=OrderStatus.SHIPPED,
    )
    state_machine = OrderStateMachine()

    state_machine.transition(
        order,
        OrderStatus.DELIVERED,
    )

    assert order.status == OrderStatus.DELIVERED
    assert isinstance(order.completed_at, datetime)


def test_created_can_transition_to_cancelled():
    order = Order("ORD-001")
    state_machine = OrderStateMachine()

    state_machine.transition(
        order,
        OrderStatus.CANCELLED,
    )

    assert order.status == OrderStatus.CANCELLED
    assert isinstance(order.cancelled_at, datetime)


def test_paid_can_transition_to_cancelled():
    order = Order(
        "ORD-001",
        status=OrderStatus.PAID,
    )
    state_machine = OrderStateMachine()

    state_machine.transition(
        order,
        OrderStatus.CANCELLED,
    )

    assert order.status == OrderStatus.CANCELLED
    assert isinstance(order.cancelled_at, datetime)


def test_created_cannot_transition_to_shipped():
    order = Order("ORD-001")
    state_machine = OrderStateMachine()

    with pytest.raises(
        ValueError,
        match="Invalid order transition",
    ):
        state_machine.transition(
            order,
            OrderStatus.SHIPPED,
        )


def test_created_cannot_transition_to_delivered():
    order = Order("ORD-001")
    state_machine = OrderStateMachine()

    with pytest.raises(ValueError):
        state_machine.transition(
            order,
            OrderStatus.DELIVERED,
        )


def test_paid_cannot_transition_to_delivered():
    order = Order(
        "ORD-001",
        status=OrderStatus.PAID,
    )
    state_machine = OrderStateMachine()

    with pytest.raises(ValueError):
        state_machine.transition(
            order,
            OrderStatus.DELIVERED,
        )


def test_shipped_cannot_transition_to_paid():
    order = Order(
        "ORD-001",
        status=OrderStatus.SHIPPED,
    )
    state_machine = OrderStateMachine()

    with pytest.raises(ValueError):
        state_machine.transition(
            order,
            OrderStatus.PAID,
        )


def test_delivered_cannot_transition_to_created():
    order = Order(
        "ORD-001",
        status=OrderStatus.DELIVERED,
    )
    state_machine = OrderStateMachine()

    with pytest.raises(ValueError):
        state_machine.transition(
            order,
            OrderStatus.CREATED,
        )


def test_delivered_cannot_transition_to_paid():
    order = Order(
        "ORD-001",
        status=OrderStatus.DELIVERED,
    )
    state_machine = OrderStateMachine()

    with pytest.raises(ValueError):
        state_machine.transition(
            order,
            OrderStatus.PAID,
        )


def test_delivered_cannot_transition_to_shipped():
    order = Order(
        "ORD-001",
        status=OrderStatus.DELIVERED,
    )
    state_machine = OrderStateMachine()

    with pytest.raises(ValueError):
        state_machine.transition(
            order,
            OrderStatus.SHIPPED,
        )


def test_cancelled_is_terminal():
    order = Order(
        "ORD-001",
        status=OrderStatus.CANCELLED,
    )
    state_machine = OrderStateMachine()

    with pytest.raises(ValueError):
        state_machine.transition(
            order,
            OrderStatus.CREATED,
        )

    with pytest.raises(ValueError):
        state_machine.transition(
            order,
            OrderStatus.PAID,
        )


def test_order_status_cannot_be_assigned_directly():
    order = Order("ORD-001")

    with pytest.raises(AttributeError):
        order.status = OrderStatus.PAID


def test_can_transition_returns_true_for_valid_transition():
    state_machine = OrderStateMachine()

    assert state_machine.can_transition(
        OrderStatus.CREATED,
        OrderStatus.PAID,
    )

    assert state_machine.can_transition(
        OrderStatus.PAID,
        OrderStatus.SHIPPED,
    )

    assert state_machine.can_transition(
        OrderStatus.SHIPPED,
        OrderStatus.DELIVERED,
    )


def test_can_transition_returns_false_for_invalid_transition():
    state_machine = OrderStateMachine()

    assert not state_machine.can_transition(
        OrderStatus.CREATED,
        OrderStatus.DELIVERED,
    )

    assert not state_machine.can_transition(
        OrderStatus.DELIVERED,
        OrderStatus.PAID,
    )