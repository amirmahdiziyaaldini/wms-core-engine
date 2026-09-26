from datetime import datetime
from decimal import Decimal

import pytest

from app.domain.enums.qc_result import QCResult
from app.domain.enums.return_reason import ReturnReason
from app.domain.enums.return_status import ReturnStatus
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.domain.models.return_item import ReturnItem
from app.domain.models.return_request import ReturnRequest
from app.services.qc_service import QCService


def create_return_request() -> ReturnRequest:
    order = Order(
        order_id="ORD-001",
        customer_id="CUS-001",
    )

    order.add_item(
        OrderItem(
            item_id="ITEM-001",
            sku="LAPTOP-01",
            quantity=1,
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


def move_to_qc(return_request: ReturnRequest) -> None:
    return_request._set_status(
        ReturnStatus.RECEIVED_AT_WAREHOUSE,
        datetime(2026, 9, 1, 10, 0),
    )

    return_request._set_status(
        ReturnStatus.QC_INSPECTION,
        datetime(2026, 9, 1, 11, 0),
    )


def test_qc_result_can_be_recorded_in_qc_inspection():
    service = QCService()
    return_request = create_return_request()

    move_to_qc(return_request)

    timestamp = datetime(2026, 9, 1, 12, 0)

    service.record_result(
        return_request=return_request,
        result=QCResult.APPROVED,
        note="Product is healthy",
        timestamp=timestamp,
    )

    assert return_request.qc_result == QCResult.APPROVED
    assert return_request.qc_note == "Product is healthy"
    assert return_request.qc_at == timestamp


def test_inherent_defect_result_can_be_recorded():
    service = QCService()
    return_request = create_return_request()

    move_to_qc(return_request)

    service.record_result(
        return_request=return_request,
        result=QCResult.INHERENT_DEFECT,
        note="Internal hardware defect",
    )

    assert return_request.qc_result == QCResult.INHERENT_DEFECT


def test_rejected_result_can_be_recorded():
    service = QCService()
    return_request = create_return_request()

    move_to_qc(return_request)

    service.record_result(
        return_request=return_request,
        result=QCResult.REJECTED,
        note="Return conditions were not met",
    )

    assert return_request.qc_result == QCResult.REJECTED


def test_qc_result_cannot_be_recorded_before_qc_inspection():
    service = QCService()
    return_request = create_return_request()

    with pytest.raises(
        ValueError,
        match="QC result can only be recorded during QC inspection",
    ):
        service.record_result(
            return_request=return_request,
            result=QCResult.APPROVED,
        )


def test_qc_result_cannot_be_recorded_after_qc_inspection():
    service = QCService()
    return_request = create_return_request()

    move_to_qc(return_request)

    return_request._set_status(
        ReturnStatus.APPROVED,
        datetime(2026, 9, 1, 13, 0),
    )

    with pytest.raises(
        ValueError,
        match="QC result can only be recorded during QC inspection",
    ):
        service.record_result(
            return_request=return_request,
            result=QCResult.APPROVED,
        )


def test_qc_note_cannot_be_empty():
    service = QCService()
    return_request = create_return_request()

    move_to_qc(return_request)

    with pytest.raises(
        ValueError,
        match="QC note cannot be empty",
    ):
        service.record_result(
            return_request=return_request,
            result=QCResult.APPROVED,
            note="   ",
        )


def test_qc_result_must_be_qc_result_enum():
    service = QCService()
    return_request = create_return_request()

    move_to_qc(return_request)

    with pytest.raises(
        ValueError,
        match="QC result must be a QCResult",
    ):
        service.record_result(
            return_request=return_request,
            result="approved",
        )