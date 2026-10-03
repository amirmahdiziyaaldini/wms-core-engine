from datetime import datetime

import pytest

from app.domain.enums.order_status import OrderStatus
from app.domain.models.order import Order
from app.domain.states.order_state_machine import OrderStateMachine


def test_created_can_transition_to_paid():
    order = Order("ORD-001")
    state_machine = OrderStateMachine()
    timestamp = datetime(2026, 9, 29, 10, 0)

    state_machine.transition(
        order,
        OrderStatus.PAID,
        timestamp=timestamp,
    )

    assert order.status == OrderStatus.PAID
    assert order.paid_at == timestamp


def test_created_can_transition_to_reserved():
    order = Order("ORD-001")
    state_machine = OrderStateMachine()
    timestamp = datetime(2026, 9, 29, 10, 0)

    state_machine.transition(
        order,
        OrderStatus.RESERVED,
        timestamp=timestamp,
    )

    assert order.status == OrderStatus.RESERVED
    assert order.reserved_at == timestamp


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
    timestamp = datetime(2026, 9, 29, 11, 0)

    state_machine.transition(
        order,
        OrderStatus.PAID,
        timestamp=timestamp,
    )

    assert order.status == OrderStatus.PAID
    assert order.paid_at == timestamp


def test_reserved_can_transition_to_cancelled():
    order = Order(
        "ORD-001",
        status=OrderStatus.RESERVED,
    )
    state_machine = OrderStateMachine()
    timestamp = datetime(2026, 9, 29, 12, 0)

    state_machine.transition(
        order,
        OrderStatus.CANCELLED,
        timestamp=timestamp,
    )

    assert order.status == OrderStatus.CANCELLED
    assert order.cancelled_at == timestamp


def test_paid_can_transition_to_shipped():
    order = Order(
        "ORD-001",
        status=OrderStatus.PAID,
    )
    state_machine = OrderStateMachine()
    timestamp = datetime(2026, 9, 29, 13, 0)

    state_machine.transition(
        order,
        OrderStatus.SHIPPED,
        timestamp=timestamp,
    )

    assert order.status == OrderStatus.SHIPPED
    assert order.shipped_at == timestamp


def test_paid_can_transition_to_cancelled():
    order = Order(
        "ORD-001",
        status=OrderStatus.PAID,
    )
    state_machine = OrderStateMachine()
    timestamp = datetime(2026, 9, 29, 14, 0)

    state_machine.transition(
        order,
        OrderStatus.CANCELLED,
        timestamp=timestamp,
    )

    assert order.status == OrderStatus.CANCELLED
    assert order.cancelled_at == timestamp


def test_shipped_can_transition_to_delivered():
    order = Order(
        "ORD-001",
        status=OrderStatus.SHIPPED,
    )
    state_machine = OrderStateMachine()
    timestamp = datetime(2026, 9, 29, 15, 0)

    state_machine.transition(
        order,
        OrderStatus.DELIVERED,
        timestamp=timestamp,
    )

    assert order.status == OrderStatus.DELIVERED
    assert order.delivered_at == timestamp
    assert order.completed_at == timestamp


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
    "status",
    [
        OrderStatus.CREATED,
        OrderStatus.RESERVED,
        OrderStatus.PAID,
        OrderStatus.SHIPPED,
        OrderStatus.DELIVERED,
        OrderStatus.CANCELLED,
    ],
)
def test_order_cannot_transition_to_same_status(status):
    state_machine = OrderStateMachine()

    assert not state_machine.can_transition(
        status,
        status,
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
    timestamp = datetime(2026, 9, 29, 10, 0)

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


def test_delivered_is_terminal():
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

    with pytest.raises(ValueError):
        state_machine.transition(
            order,
            OrderStatus.CANCELLED,
        )


def test_order_status_cannot_be_assigned_directly():
    order = Order("ORD-001")

    with pytest.raises(AttributeError):
        order.status = OrderStatus.PAID


def test_can_transition_rejects_invalid_current_status():
    state_machine = OrderStateMachine()

    with pytest.raises(
        ValueError,
        match="Current status must be an OrderStatus",
    ):
        state_machine.can_transition(
            "created",
            OrderStatus.PAID,
        )


def test_can_transition_rejects_invalid_target_status():
    state_machine = OrderStateMachine()

    with pytest.raises(
        ValueError,
        match="Target status must be an OrderStatus",
    ):
        state_machine.can_transition(
            OrderStatus.CREATED,
            "paid",
        )


def test_transition_rejects_invalid_order():
    state_machine = OrderStateMachine()

    with pytest.raises(
        ValueError,
        match="Order must be an Order",
    ):
        state_machine.transition(
            "ORD-001",
            OrderStatus.PAID,
        )


def test_transition_rejects_invalid_target_status():
    order = Order("ORD-001")
    state_machine = OrderStateMachine()

    with pytest.raises(
        ValueError,
        match="Target status must be an OrderStatus",
    ):
        state_machine.transition(
            order,
            "paid",
        )


def test_transition_rejects_invalid_timestamp():
    order = Order("ORD-001")
    state_machine = OrderStateMachine()

    with pytest.raises(
        ValueError,
        match="Timestamp must be a datetime",
    ):
        state_machine.transition(
            order,
            OrderStatus.PAID,
            timestamp="2026-09-29",
        )

    assert order.status == OrderStatus.CREATED
    assert order.paid_at is None


def test_invalid_timestamp_does_not_change_order_state():
    order = Order("ORD-001")
    state_machine = OrderStateMachine()

    with pytest.raises(ValueError):
        state_machine.transition(
            order,
            OrderStatus.PAID,
            timestamp="invalid",
        )

    assert order.status == OrderStatus.CREATED
    assert order.paid_at is None


def test_transition_without_timestamp_sets_datetime():
    order = Order("ORD-001")
    state_machine = OrderStateMachine()

    state_machine.transition(
        order,
        OrderStatus.PAID,
    )

    assert order.status == OrderStatus.PAID
    assert isinstance(order.paid_at, datetime)


def test_delivered_sets_delivered_and_completed_to_same_timestamp():
    order = Order(
        "ORD-001",
        status=OrderStatus.SHIPPED,
    )
    state_machine = OrderStateMachine()
    timestamp = datetime(2026, 9, 29, 18, 30)

    state_machine.transition(
        order,
        OrderStatus.DELIVERED,
        timestamp=timestamp,
    )

    assert order.delivered_at == timestamp
    assert order.completed_at == timestamp


def test_transition_preserves_previous_timestamps():
    order = Order("ORD-001")
    state_machine = OrderStateMachine()

    reserved_at = datetime(2026, 9, 29, 10, 0)
    paid_at = datetime(2026, 9, 29, 11, 0)
    shipped_at = datetime(2026, 9, 29, 12, 0)
    delivered_at = datetime(2026, 9, 29, 13, 0)

    state_machine.transition(
        order,
        OrderStatus.RESERVED,
        timestamp=reserved_at,
    )

    state_machine.transition(
        order,
        OrderStatus.PAID,
        timestamp=paid_at,
    )

    state_machine.transition(
        order,
        OrderStatus.SHIPPED,
        timestamp=shipped_at,
    )

    state_machine.transition(
        order,
        OrderStatus.DELIVERED,
        timestamp=delivered_at,
    )

    assert order.reserved_at == reserved_at
    assert order.paid_at == paid_at
    assert order.shipped_at == shipped_at
    assert order.delivered_at == delivered_at
    assert order.completed_at == delivered_at