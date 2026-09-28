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


def test_created_can_transition_to_reserved():
    order = Order("ORD-001")
    state_machine = OrderStateMachine()

    state_machine.transition(
        order,
        OrderStatus.RESERVED,
    )

    assert order.status == OrderStatus.RESERVED
    assert isinstance(order.reserved_at, datetime)


def test_reserved_can_transition_to_created():
    order = Order(
        "ORD-001",
        status=OrderStatus.RESERVED,
    )
    state_machine = OrderStateMachine()

    state_machine.transition(
        order,
        OrderStatus.CREATED,
    )

    assert order.status == OrderStatus.CREATED


def test_reserved_can_transition_to_paid():
    order = Order(
        "ORD-001",
        status=OrderStatus.RESERVED,
    )
    state_machine = OrderStateMachine()

    state_machine.transition(
        order,
        OrderStatus.PAID,
    )

    assert order.status == OrderStatus.PAID
    assert isinstance(order.paid_at, datetime)


def test_reserved_can_transition_to_cancelled():
    order = Order(
        "ORD-001",
        status=OrderStatus.RESERVED,
    )
    state_machine = OrderStateMachine()

    state_machine.transition(
        order,
        OrderStatus.CANCELLED,
    )

    assert order.status == OrderStatus.CANCELLED
    assert isinstance(order.cancelled_at, datetime)


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


@pytest.mark.parametrize(
    "current_status,target_status",
    [
        (
            OrderStatus.CREATED,
            OrderStatus.PAID,
        ),
        (
            OrderStatus.CREATED,
            OrderStatus.RESERVED,
        ),
        (
            OrderStatus.CREATED,
            OrderStatus.CANCELLED,
        ),
        (
            OrderStatus.RESERVED,
            OrderStatus.CREATED,
        ),
        (
            OrderStatus.RESERVED,
            OrderStatus.PAID,
        ),
        (
            OrderStatus.RESERVED,
            OrderStatus.CANCELLED,
        ),
        (
            OrderStatus.PAID,
            OrderStatus.SHIPPED,
        ),
        (
            OrderStatus.PAID,
            OrderStatus.CANCELLED,
        ),
        (
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
        ),
    ],
)
def test_all_valid_order_transitions(
    current_status,
    target_status,
):
    state_machine = OrderStateMachine()

    assert state_machine.can_transition(
        current_status,
        target_status,
    )


@pytest.mark.parametrize(
    "current_status,target_status",
    [
        (
            OrderStatus.CREATED,
            OrderStatus.SHIPPED,
        ),
        (
            OrderStatus.CREATED,
            OrderStatus.DELIVERED,
        ),
        (
            OrderStatus.RESERVED,
            OrderStatus.SHIPPED,
        ),
        (
            OrderStatus.RESERVED,
            OrderStatus.DELIVERED,
        ),
        (
            OrderStatus.PAID,
            OrderStatus.CREATED,
        ),
        (
            OrderStatus.PAID,
            OrderStatus.RESERVED,
        ),
        (
            OrderStatus.PAID,
            OrderStatus.DELIVERED,
        ),
        (
            OrderStatus.SHIPPED,
            OrderStatus.CREATED,
        ),
        (
            OrderStatus.SHIPPED,
            OrderStatus.RESERVED,
        ),
        (
            OrderStatus.SHIPPED,
            OrderStatus.PAID,
        ),
        (
            OrderStatus.SHIPPED,
            OrderStatus.CANCELLED,
        ),
        (
            OrderStatus.DELIVERED,
            OrderStatus.CREATED,
        ),
        (
            OrderStatus.DELIVERED,
            OrderStatus.RESERVED,
        ),
        (
            OrderStatus.DELIVERED,
            OrderStatus.PAID,
        ),
        (
            OrderStatus.DELIVERED,
            OrderStatus.SHIPPED,
        ),
        (
            OrderStatus.DELIVERED,
            OrderStatus.CANCELLED,
        ),
        (
            OrderStatus.CANCELLED,
            OrderStatus.CREATED,
        ),
        (
            OrderStatus.CANCELLED,
            OrderStatus.RESERVED,
        ),
        (
            OrderStatus.CANCELLED,
            OrderStatus.PAID,
        ),
        (
            OrderStatus.CANCELLED,
            OrderStatus.SHIPPED,
        ),
        (
            OrderStatus.CANCELLED,
            OrderStatus.DELIVERED,
        ),
    ],
)
def test_all_invalid_order_transitions(
    current_status,
    target_status,
):
    state_machine = OrderStateMachine()

    assert not state_machine.can_transition(
        current_status,
        target_status,
    )


@pytest.mark.parametrize(
    "current_status,target_status",
    [
        (
            OrderStatus.CREATED,
            OrderStatus.SHIPPED,
        ),
        (
            OrderStatus.CREATED,
            OrderStatus.DELIVERED,
        ),
        (
            OrderStatus.PAID,
            OrderStatus.DELIVERED,
        ),
        (
            OrderStatus.SHIPPED,
            OrderStatus.PAID,
        ),
        (
            OrderStatus.DELIVERED,
            OrderStatus.CREATED,
        ),
        (
            OrderStatus.CANCELLED,
            OrderStatus.PAID,
        ),
    ],
)
def test_invalid_transition_does_not_change_order_status(
    current_status,
    target_status,
):
    order = Order(
        "ORD-001",
        status=current_status,
    )
    state_machine = OrderStateMachine()

    with pytest.raises(ValueError):
        state_machine.transition(
            order,
            target_status,
        )

    assert order.status == current_status


def test_invalid_transition_does_not_change_existing_timestamps():
    order = Order("ORD-001")
    state_machine = OrderStateMachine()
    timestamp = datetime(2026, 9, 27, 10, 0)

    state_machine.transition(
        order,
        OrderStatus.PAID,
        timestamp=timestamp,
    )

    paid_at_before = order.paid_at
    shipped_at_before = order.shipped_at
    cancelled_at_before = order.cancelled_at

    with pytest.raises(ValueError):
        state_machine.transition(
            order,
            OrderStatus.DELIVERED,
        )

    assert order.status == OrderStatus.PAID
    assert order.paid_at == paid_at_before
    assert order.shipped_at == shipped_at_before
    assert order.cancelled_at == cancelled_at_before


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