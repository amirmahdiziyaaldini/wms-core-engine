from datetime import date, datetime
from decimal import Decimal

import pytest

from app.domain.enums.warehouse_type import WarehouseType
from app.domain.enums.order_status import OrderStatus
from app.domain.models.base_product import BaseProduct
from app.domain.models.batch import Batch
from app.domain.models.inventory import Inventory
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.domain.models.warehouse import Warehouse
from app.services.order_service import OrderService


def create_product(
    sku: str = "SKU-001",
) -> BaseProduct:
    return BaseProduct(
        sku=sku,
        name="Product",
        barcode=f"BAR-{sku}",
        category="General",
        base_price=Decimal("100"),
    )


def create_inventory(
    quantity: int = 10,
    serial_numbers: list[str] | None = None,
) -> Inventory:
    warehouse = Warehouse(
        warehouse_id="WH-001",
        name="Main Warehouse",
        location="Tehran",
        warehouse_type=WarehouseType.CENTRAL,
    )

    inventory = Inventory(
        warehouse=warehouse
    )

    inventory.add_batch(
        Batch(
            batch_id="BATCH-001",
            product=create_product(),
            quantity=quantity,
            entry_date=date(2026, 1, 1),
            serial_numbers=serial_numbers,
        )
    )

    return inventory


def create_order(
    quantity: int = 2,
) -> Order:
    order = Order(
        order_id="ORD-001"
    )

    order.add_item(
        OrderItem(
            item_id="ITEM-001",
            sku="SKU-001",
            quantity=quantity,
        )
    )

    order.items[0].set_price_snapshot(
        Decimal("100")
    )

    return order


def create_paid_order(
    quantity: int = 2,
):
    order = create_order(
        quantity=quantity
    )

    service = OrderService()

    inventory = create_inventory(
        quantity=10
    )

    service.reserve_order(
        order=order,
        inventory=inventory,
    )

    service.mark_as_paid(
        order=order,
        transaction_reference="PAY-001",
        amount=Decimal("200"),
    )

    return service, order, inventory


def test_ship_order_consumes_inventory():
    service, order, inventory = create_paid_order()

    assert inventory.get_physical_stock("SKU-001") == 10
    assert inventory.get_reserved_stock("SKU-001") == 2

    shipment = service.ship_order(
        order=order,
        inventory=inventory,
        timestamp=datetime(2026, 9, 26, 10, 0),
    )

    assert order.status == OrderStatus.SHIPPED
    assert inventory.get_physical_stock("SKU-001") == 8
    assert inventory.get_reserved_stock("SKU-001") == 0
    assert shipment.order_id == "ORD-001"


def test_ship_order_records_shipped_at():
    service, order, inventory = create_paid_order()

    service.ship_order(
        order=order,
        inventory=inventory,
        timestamp=datetime(2026, 9, 26, 10, 0),
    )

    assert order.shipped_at is not None
    assert isinstance(
        order.shipped_at,
        datetime,
    )


def test_delivery_changes_order_status():
    service, order, inventory = create_paid_order()

    service.ship_order(
        order=order,
        inventory=inventory,
        timestamp=datetime(2026, 9, 26, 10, 0),
    )

    service.deliver_order(
        order=order,
        timestamp=datetime(2026, 9, 27, 10, 0),
    )

    assert order.status == OrderStatus.DELIVERED


def test_delivery_records_delivered_at():
    service, order, inventory = create_paid_order()

    service.ship_order(
        order=order,
        inventory=inventory,
        timestamp=datetime(2026, 9, 26, 10, 0),
    )

    service.deliver_order(
        order=order,
        timestamp=datetime(2026, 9, 27, 10, 0),
    )

    assert order.delivered_at is not None
    assert isinstance(
        order.delivered_at,
        datetime,
    )


def test_delivery_does_not_change_inventory_again():
    service, order, inventory = create_paid_order()

    service.ship_order(
        order=order,
        inventory=inventory,
        timestamp=datetime(2026, 9, 26, 10, 0),
    )

    physical_after_shipment = (
        inventory.get_physical_stock("SKU-001")
    )

    service.deliver_order(
        order=order,
        timestamp=datetime(2026, 9, 27, 10, 0),
    )

    assert (
        inventory.get_physical_stock("SKU-001")
        == physical_after_shipment
    )


def test_delivery_before_shipment_is_rejected():
    service = OrderService()
    order = create_order()

    with pytest.raises(
        ValueError,
        match="Only shipped orders can be delivered",
    ):
        service.deliver_order(
            order=order,
            timestamp=datetime(2026, 9, 27, 10, 0),
        )


def test_ship_order_requires_paid_order():
    service = OrderService()
    order = create_order()
    inventory = create_inventory()

    service.reserve_order(
        order=order,
        inventory=inventory,
    )

    with pytest.raises(
        ValueError,
        match="Only paid orders can be shipped",
    ):
        service.ship_order(
            order=order,
            inventory=inventory,
            timestamp=datetime(2026, 9, 26, 10, 0),
        )


def test_ship_order_requires_reservation():
    service = OrderService()
    order = create_order()
    inventory = create_inventory()

    order._set_status(
        OrderStatus.PAID,
        datetime(2026, 9, 26, 9, 0),
    )

    with pytest.raises(
        ValueError,
        match="Order has no active reservations",
    ):
        service.ship_order(
            order=order,
            inventory=inventory,
            timestamp=datetime(2026, 9, 26, 10, 0),
        )


def test_ship_order_rejects_incomplete_reservations():
    service = OrderService()
    order = create_order()
    inventory = create_inventory()

    order._set_status(
        OrderStatus.PAID,
        datetime(2026, 9, 26, 9, 0),
    )

    inventory.reserve(
        reservation_id="RES-WRONG",
        sku="SKU-001",
        quantity=2,
    )

    with pytest.raises(
        ValueError,
        match="Order has no active reservations",
    ):
        service.ship_order(
            order=order,
            inventory=inventory,
            timestamp=datetime(2026, 9, 26, 10, 0),
        )


def test_serial_numbers_are_saved_in_shipment_history():
    service = OrderService()

    inventory = create_inventory(
        quantity=2,
        serial_numbers=[
            "SERIAL-001",
            "SERIAL-002",
        ],
    )

    order = create_order(
        quantity=2
    )

    service.reserve_order(
        order=order,
        inventory=inventory,
    )

    service.mark_as_paid(
        order=order,
        transaction_reference="PAY-001",
        amount=Decimal("200"),
    )

    shipment = service.ship_order(
        order=order,
        inventory=inventory,
        timestamp=datetime(2026, 9, 26, 10, 0),
    )

    assert shipment.serial_numbers == [
        "SERIAL-001",
        "SERIAL-002",
    ]


def test_serial_shipment_history_is_retrievable():
    service = OrderService()

    inventory = create_inventory(
        quantity=2,
        serial_numbers=[
            "SERIAL-001",
            "SERIAL-002",
        ],
    )

    order = create_order(
        quantity=2
    )

    service.reserve_order(
        order=order,
        inventory=inventory,
    )

    service.mark_as_paid(
        order=order,
        transaction_reference="PAY-001",
        amount=Decimal("200"),
    )

    service.ship_order(
        order=order,
        inventory=inventory,
        timestamp=datetime(2026, 9, 26, 10, 0),
    )

    history = service.get_serial_shipment_history(
        "SERIAL-001"
    )

    assert len(history) == 1
    assert history[0].order_id == "ORD-001"


def test_order_shipment_history_is_retrievable():
    service, order, inventory = create_paid_order()

    service.ship_order(
        order=order,
        inventory=inventory,
        timestamp=datetime(2026, 9, 26, 10, 0),
    )

    history = service.get_order_shipments(
        "ORD-001"
    )

    assert len(history) == 1
    assert history[0].shipment_id == "SHP-ORD-001"


def test_second_shipment_is_rejected():
    service, order, inventory = create_paid_order()

    service.ship_order(
        order=order,
        inventory=inventory,
        timestamp=datetime(2026, 9, 26, 10, 0),
    )

    with pytest.raises(
        ValueError,
        match="Order has already been shipped",
    ):
        service.ship_order(
            order=order,
            inventory=inventory,
            timestamp=datetime(2026, 9, 26, 11, 0),
        )


def test_second_delivery_is_rejected():
    service, order, inventory = create_paid_order()

    service.ship_order(
        order=order,
        inventory=inventory,
        timestamp=datetime(2026, 9, 26, 10, 0),
    )

    service.deliver_order(
        order=order,
        timestamp=datetime(2026, 9, 27, 10, 0),
    )

    with pytest.raises(
        ValueError,
        match="Only shipped orders can be delivered",
    ):
        service.deliver_order(
            order=order,
            timestamp=datetime(2026, 9, 28, 10, 0),
        )