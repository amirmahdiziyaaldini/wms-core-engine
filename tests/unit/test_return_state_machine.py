from datetime import datetime
from decimal import Decimal

import pytest

from app.domain.enums.return_reason import ReturnReason
from app.domain.enums.return_status import ReturnStatus
from app.domain.exceptions.invalid_return_state import InvalidReturnStateError
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.domain.models.return_item import ReturnItem
from app.domain.models.return_request import ReturnRequest
from app.domain.states.return_state_machine import ReturnStateMachine


def create_return_request() -> ReturnRequest:
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

    return ReturnRequest(
        return_id="RET-001",
        order=order,
        reason=ReturnReason.DAMAGED,
        items=[
            ReturnItem(
                sku="LAPTOP-01",
                quantity=1,
            )
        ],
    )


def test_return_request_starts_as_requested():
    return_request = create_return_request()

    assert return_request.status == ReturnStatus.REQUESTED


def test_main_return_flow():
    state_machine = ReturnStateMachine()
    return_request = create_return_request()

    requested_at = datetime(2026, 9, 1, 10, 0)
    received_at = datetime(2026, 9, 2, 10, 0)
    qc_at = datetime(2026, 9, 3, 10, 0)
    approved_at = datetime(2026, 9, 4, 10, 0)
    refunded_at = datetime(2026, 9, 5, 10, 0)

    return_request.requested_at = requested_at

    state_machine.transition(
        return_request,
        ReturnStatus.RECEIVED_AT_WAREHOUSE,
        received_at,
    )

    state_machine.transition(
        return_request,
        ReturnStatus.QC_INSPECTION,
        qc_at,
    )

    state_machine.transition(
        return_request,
        ReturnStatus.APPROVED,
        approved_at,
    )

    state_machine.transition(
        return_request,
        ReturnStatus.REFUNDED,
        refunded_at,
    )

    assert return_request.status == ReturnStatus.REFUNDED
    assert return_request.received_at_warehouse == received_at
    assert return_request.qc_inspection_at == qc_at
    assert return_request.approved_at == approved_at
    assert return_request.refunded_at == refunded_at


def test_request_can_be_rejected():
    state_machine = ReturnStateMachine()
    return_request = create_return_request()

    rejected_at = datetime(2026, 9, 2, 12, 0)

    state_machine.transition(
        return_request,
        ReturnStatus.REJECTED,
        rejected_at,
    )

    assert return_request.status == ReturnStatus.REJECTED
    assert return_request.rejected_at == rejected_at


def test_received_return_can_be_rejected():
    state_machine = ReturnStateMachine()
    return_request = create_return_request()

    received_at = datetime(2026, 9, 2, 10, 0)
    rejected_at = datetime(2026, 9, 2, 12, 0)

    state_machine.transition(
        return_request,
        ReturnStatus.RECEIVED_AT_WAREHOUSE,
        received_at,
    )

    state_machine.transition(
        return_request,
        ReturnStatus.REJECTED,
        rejected_at,
    )

    assert return_request.status == ReturnStatus.REJECTED
    assert return_request.received_at_warehouse == received_at
    assert return_request.rejected_at == rejected_at


def test_qc_return_can_be_rejected():
    state_machine = ReturnStateMachine()
    return_request = create_return_request()

    state_machine.transition(
        return_request,
        ReturnStatus.RECEIVED_AT_WAREHOUSE,
        datetime(2026, 9, 2, 10, 0),
    )

    state_machine.transition(
        return_request,
        ReturnStatus.QC_INSPECTION,
        datetime(2026, 9, 3, 10, 0),
    )

    rejected_at = datetime(2026, 9, 3, 12, 0)

    state_machine.transition(
        return_request,
        ReturnStatus.REJECTED,
        rejected_at,
    )

    assert return_request.status == ReturnStatus.REJECTED
    assert return_request.rejected_at == rejected_at


def test_invalid_transition_raises_invalid_return_state_error():
    state_machine = ReturnStateMachine()
    return_request = create_return_request()

    with pytest.raises(InvalidReturnStateError):
        state_machine.transition(
            return_request,
            ReturnStatus.APPROVED,
        )


def test_approved_return_cannot_be_rejected():
    state_machine = ReturnStateMachine()
    return_request = create_return_request()

    state_machine.transition(
        return_request,
        ReturnStatus.RECEIVED_AT_WAREHOUSE,
    )

    state_machine.transition(
        return_request,
        ReturnStatus.QC_INSPECTION,
    )

    state_machine.transition(
        return_request,
        ReturnStatus.APPROVED,
    )

    with pytest.raises(InvalidReturnStateError):
        state_machine.transition(
            return_request,
            ReturnStatus.REJECTED,
        )


def test_refunded_return_cannot_change_state():
    state_machine = ReturnStateMachine()
    return_request = create_return_request()

    state_machine.transition(
        return_request,
        ReturnStatus.RECEIVED_AT_WAREHOUSE,
    )

    state_machine.transition(
        return_request,
        ReturnStatus.QC_INSPECTION,
    )

    state_machine.transition(
        return_request,
        ReturnStatus.APPROVED,
    )

    state_machine.transition(
        return_request,
        ReturnStatus.REFUNDED,
    )

    with pytest.raises(InvalidReturnStateError):
        state_machine.transition(
            return_request,
            ReturnStatus.REJECTED,
        )


def test_can_transition():
    state_machine = ReturnStateMachine()

    assert state_machine.can_transition(
        ReturnStatus.REQUESTED,
        ReturnStatus.RECEIVED_AT_WAREHOUSE,
    ) is True

    assert state_machine.can_transition(
        ReturnStatus.RECEIVED_AT_WAREHOUSE,
        ReturnStatus.QC_INSPECTION,
    ) is True

    assert state_machine.can_transition(
        ReturnStatus.QC_INSPECTION,
        ReturnStatus.APPROVED,
    ) is True

    assert state_machine.can_transition(
        ReturnStatus.APPROVED,
        ReturnStatus.REFUNDED,
    ) is True

    assert state_machine.can_transition(
        ReturnStatus.REQUESTED,
        ReturnStatus.APPROVED,
    ) is False