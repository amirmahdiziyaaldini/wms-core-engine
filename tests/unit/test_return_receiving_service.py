from datetime import datetime
from decimal import Decimal

import pytest

from app.domain.enums.order_status import OrderStatus
from app.domain.enums.return_reason import ReturnReason
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.domain.models.return_item import ReturnItem
from app.domain.models.return_request import ReturnRequest
from app.domain.models.shipment import Shipment
from app.repositories.shipment_repository import ShipmentRepository
from app.services.return_receiving_service import ReturnReceivingService


def create_delivered_order() -> Order:
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
        datetime(2026, 9, 1, 10, 0),
    )

    order._set_status(
        OrderStatus.DELIVERED,
        datetime(2026, 9, 2, 10, 0),
    )

    return order


def create_return_request(
    quantity: int = 1,
) -> ReturnRequest:
    return ReturnRequest(
        return_id="RET-001",
        order=create_delivered_order(),
        reason=ReturnReason.DAMAGED,
        items=[
            ReturnItem(
                sku="LAPTOP-01",
                quantity=quantity,
            )
        ],
    )


def test_received_item_is_stored_in_return_quarantine():
    service = ReturnReceivingService()
    return_request = create_return_request()

    receipt = service.receive(
        return_request=return_request,
        sku="LAPTOP-01",
        quantity=1,
    )

    assert receipt.status == "received_at_warehouse"
    assert receipt.location == "RETURN_QUARANTINE"
    assert receipt.quantity == 1


def test_received_item_does_not_enter_available_stock():
    service = ReturnReceivingService()
    return_request = create_return_request()

    receipt = service.receive(
        return_request=return_request,
        sku="LAPTOP-01",
        quantity=1,
    )

    assert receipt.location != "AVAILABLE"
    assert receipt.status == "received_at_warehouse"


def test_received_quantity_cannot_exceed_requested_quantity():
    service = ReturnReceivingService()
    return_request = create_return_request(quantity=1)

    with pytest.raises(
        ValueError,
        match="Received quantity cannot exceed requested quantity",
    ):
        service.receive(
            return_request=return_request,
            sku="LAPTOP-01",
            quantity=2,
        )


def test_unknown_sku_cannot_be_received():
    service = ReturnReceivingService()
    return_request = create_return_request()

    with pytest.raises(
        ValueError,
        match="SKU UNKNOWN-01 is not part of the return request",
    ):
        service.receive(
            return_request=return_request,
            sku="UNKNOWN-01",
            quantity=1,
        )


def test_serial_received_must_exist_in_original_shipment():
    shipment_repository = ShipmentRepository()

    shipment_repository.save(
        Shipment(
            shipment_id="SHIP-001",
            order_id="ORD-001",
            warehouse_id="WH-001",
            shipped_at=datetime(2026, 9, 1, 10, 0),
            serial_numbers=[
                "SERIAL-001",
                "SERIAL-002",
            ],
        )
    )

    service = ReturnReceivingService(
        shipment_repository=shipment_repository,
    )

    return_request = create_return_request()

    receipt = service.receive(
        return_request=return_request,
        sku="LAPTOP-01",
        quantity=1,
        serial_numbers=["SERIAL-001"],
    )

    assert receipt.serial_numbers == ["SERIAL-001"]


def test_unknown_serial_cannot_be_received():
    shipment_repository = ShipmentRepository()

    shipment_repository.save(
        Shipment(
            shipment_id="SHIP-001",
            order_id="ORD-001",
            warehouse_id="WH-001",
            shipped_at=datetime(2026, 9, 1, 10, 0),
            serial_numbers=[
                "SERIAL-001",
            ],
        )
    )

    service = ReturnReceivingService(
        shipment_repository=shipment_repository,
    )

    return_request = create_return_request()

    with pytest.raises(
        ValueError,
        match="Serial number SERIAL-999 was not sold in the original order",
    ):
        service.receive(
            return_request=return_request,
            sku="LAPTOP-01",
            quantity=1,
            serial_numbers=["SERIAL-999"],
        )


def test_received_quantity_for_serialized_item_must_match_serial_count():
    shipment_repository = ShipmentRepository()

    shipment_repository.save(
        Shipment(
            shipment_id="SHIP-001",
            order_id="ORD-001",
            warehouse_id="WH-001",
            shipped_at=datetime(2026, 9, 1, 10, 0),
            serial_numbers=[
                "SERIAL-001",
                "SERIAL-002",
            ],
        )
    )

    service = ReturnReceivingService(
        shipment_repository=shipment_repository,
    )

    return_request = create_return_request(quantity=2)

    with pytest.raises(
        ValueError,
        match="Number of serial numbers must match quantity",
    ):
        service.receive(
            return_request=return_request,
            sku="LAPTOP-01",
            quantity=2,
            serial_numbers=["SERIAL-001"],
        )


def test_receipt_timestamp_can_be_controlled():
    service = ReturnReceivingService()
    return_request = create_return_request()

    received_at = datetime(2026, 9, 6, 15, 30)

    receipt = service.receive(
        return_request=return_request,
        sku="LAPTOP-01",
        quantity=1,
        received_at=received_at,
    )

    assert receipt.received_at == received_at