from datetime import datetime
from decimal import Decimal

import pytest

from app.domain.enums.return_reason import ReturnReason
from app.domain.enums.return_status import ReturnStatus
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.domain.models.return_item import ReturnItem
from app.domain.models.return_request import ReturnRequest


def create_order(order_id="ORD-001"):
    order = Order(
        order_id=order_id,
        customer_id="CUS-001",
    )

    order.add_item(
        OrderItem(
            item_id="ITEM-001",
            sku="LAPTOP-01",
            quantity=5,
            product_name="Laptop",
            unit_price=Decimal("100"),
        )
    )

    return order


def test_create_return_request():
    order = create_order()

    requested_at = datetime(
        2026,
        9,
        26,
        10,
        0,
    )

    request = ReturnRequest(
        return_id="RET-001",
        order=order,
        reason=ReturnReason.DAMAGED,
        items=[
            ReturnItem(
                sku="LAPTOP-01",
                quantity=2,
            )
        ],
        requested_at=requested_at,
    )

    assert request.return_id == "RET-001"
    assert request.order_id == "ORD-001"
    assert request.status == ReturnStatus.REQUESTED
    assert request.reason == ReturnReason.DAMAGED
    assert request.requested_at == requested_at
    assert len(request.items) == 1


def test_partial_return_is_allowed():
    request = ReturnRequest(
        return_id="RET-001",
        order=create_order(),
        reason=ReturnReason.CUSTOMER_CHANGED_MIND,
        items=[
            ReturnItem(
                sku="LAPTOP-01",
                quantity=2,
            )
        ],
    )

    assert request.items[0].quantity == 2


def test_full_return_is_allowed():
    request = ReturnRequest(
        return_id="RET-001",
        order=create_order(),
        reason=ReturnReason.WRONG_PRODUCT,
        items=[
            ReturnItem(
                sku="LAPTOP-01",
                quantity=5,
            )
        ],
    )

    assert request.items[0].quantity == 5


def test_return_quantity_cannot_exceed_purchased_quantity():
    with pytest.raises(
        ValueError,
        match="Return quantity for SKU LAPTOP-01 exceeds purchased quantity",
    ):
        ReturnRequest(
            return_id="RET-001",
            order=create_order(),
            reason=ReturnReason.DAMAGED,
            items=[
                ReturnItem(
                    sku="LAPTOP-01",
                    quantity=6,
                )
            ],
        )


def test_return_sku_must_exist_in_order():
    with pytest.raises(
        ValueError,
        match="SKU PHONE-01 is not part of the order",
    ):
        ReturnRequest(
            return_id="RET-001",
            order=create_order(),
            reason=ReturnReason.DAMAGED,
            items=[
                ReturnItem(
                    sku="PHONE-01",
                    quantity=1,
                )
            ],
        )


def test_previous_returns_are_counted_for_over_return_validation():
    order = create_order()

    first_return = ReturnRequest(
        return_id="RET-001",
        order=order,
        reason=ReturnReason.DAMAGED,
        items=[
            ReturnItem(
                sku="LAPTOP-01",
                quantity=3,
            )
        ],
    )

    second_return = ReturnRequest(
        return_id="RET-002",
        order=order,
        reason=ReturnReason.WRONG_PRODUCT,
        items=[
            ReturnItem(
                sku="LAPTOP-01",
                quantity=2,
            )
        ],
        previous_returns=[first_return],
    )

    assert second_return.items[0].quantity == 2


def test_previous_returns_prevent_over_return():
    order = create_order()

    first_return = ReturnRequest(
        return_id="RET-001",
        order=order,
        reason=ReturnReason.DAMAGED,
        items=[
            ReturnItem(
                sku="LAPTOP-01",
                quantity=3,
            )
        ],
    )

    with pytest.raises(
        ValueError,
        match="Return quantity for SKU LAPTOP-01 exceeds purchased quantity",
    ):
        ReturnRequest(
            return_id="RET-002",
            order=order,
            reason=ReturnReason.WRONG_PRODUCT,
            items=[
                ReturnItem(
                    sku="LAPTOP-01",
                    quantity=3,
                )
            ],
            previous_returns=[first_return],
        )


def test_previous_return_must_belong_to_same_order():
    order = create_order()
    other_order = create_order(
        order_id="ORD-002",
    )

    previous_return = ReturnRequest(
        return_id="RET-001",
        order=other_order,
        reason=ReturnReason.DAMAGED,
        items=[
            ReturnItem(
                sku="LAPTOP-01",
                quantity=1,
            )
        ],
    )

    with pytest.raises(
        ValueError,
        match="Previous return must belong to the same order",
    ):
        ReturnRequest(
            return_id="RET-002",
            order=order,
            reason=ReturnReason.DAMAGED,
            items=[
                ReturnItem(
                    sku="LAPTOP-01",
                    quantity=1,
                )
            ],
            previous_returns=[previous_return],
        )