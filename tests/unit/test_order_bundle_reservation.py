from datetime import date, datetime
from decimal import Decimal

import pytest

from app.domain.enums.order_status import OrderStatus
from app.domain.enums.warehouse_type import WarehouseType
from app.domain.models.base_product import BaseProduct
from app.domain.models.batch import Batch
from app.domain.models.bundle_component import BundleComponent
from app.domain.models.bundle_product import BundleProduct
from app.domain.models.inventory import Inventory
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.domain.models.warehouse import Warehouse
from app.services.order_service import OrderService


def create_inventory():
    warehouse = Warehouse(
        warehouse_id="WH-001",
        name="Main Warehouse",
        location="Berlin",
        warehouse_type=WarehouseType.CENTRAL,
    )

    inventory = Inventory(
        warehouse=warehouse,
    )

    book = BaseProduct(
        sku="BOOK-001",
        name="Book",
        barcode="BOOK-001",
        category="Books",
        base_price=Decimal("100"),
    )

    flash_drive = BaseProduct(
        sku="USB-001",
        name="Flash Drive",
        barcode="USB-001",
        category="Storage",
        base_price=Decimal("50"),
    )

    inventory.add_batch(
        Batch(
            batch_id="BATCH-BOOK",
            product=book,
            quantity=10,
            entry_date=date(2026, 1, 1),
        )
    )

    inventory.add_batch(
        Batch(
            batch_id="BATCH-USB",
            product=flash_drive,
            quantity=10,
            entry_date=date(2026, 1, 1),
        )
    )

    return inventory, book, flash_drive


def create_bundle(
    book,
    flash_drive,
):
    return BundleProduct(
        sku="BUNDLE-001",
        name="Study Bundle",
        barcode="BUNDLE-001",
        category="Bundle",
        base_price=Decimal("180"),
        components=[
            BundleComponent(book, 1),
            BundleComponent(flash_drive, 2),
        ],
    )


def create_order(
    quantity=2,
):
    order = Order(
        order_id="ORD-BUNDLE-001"
    )

    order.add_item(
        OrderItem(
            item_id="ITEM-BUNDLE-001",
            sku="BUNDLE-001",
            quantity=quantity,
        )
    )

    return order


def test_bundle_reservation_uses_component_stock():
    inventory, book, flash_drive = create_inventory()
    bundle = create_bundle(
        book,
        flash_drive,
    )

    order = create_order(
        quantity=2
    )

    service = OrderService()

    reservations = service.reserve_order(
        order=order,
        inventory=inventory,
        catalog={
            bundle.sku: bundle,
        },
    )

    assert order.status == OrderStatus.RESERVED
    assert len(reservations) == 2

    assert {
        reservation.sku
        for reservation in reservations
    } == {
        "BOOK-001",
        "USB-001",
    }

    assert inventory.get_reserved_stock(
        "BOOK-001"
    ) == 2

    assert inventory.get_reserved_stock(
        "USB-001"
    ) == 4

    assert inventory.get_reserved_stock(
        "BUNDLE-001"
    ) == 0

    assert inventory.get_available_stock(
        "BOOK-001"
    ) == 8

    assert inventory.get_available_stock(
        "USB-001"
    ) == 6


def test_bundle_reservation_rejects_insufficient_component_stock_atomically():
    inventory, book, flash_drive = create_inventory()
    bundle = create_bundle(
        book,
        flash_drive,
    )

    order = create_order(
        quantity=6
    )

    service = OrderService()

    with pytest.raises(
        ValueError,
        match="Insufficient available stock for SKU USB-001",
    ):
        service.reserve_order(
            order=order,
            inventory=inventory,
            catalog={
                bundle.sku: bundle,
            },
        )

    assert inventory.get_reserved_stock(
        "BOOK-001"
    ) == 0

    assert inventory.get_reserved_stock(
        "USB-001"
    ) == 0

    assert inventory.get_physical_stock(
        "BOOK-001"
    ) == 10

    assert inventory.get_physical_stock(
        "USB-001"
    ) == 10


def test_bundle_can_be_shipped_using_component_reservations():
    inventory, book, flash_drive = create_inventory()

    bundle = create_bundle(
        book,
        flash_drive,
    )

    order = create_order(
        quantity=2
    )

    order.items[0].set_price_snapshot(
        bundle.base_price
    )

    service = OrderService()

    service.reserve_order(
        order=order,
        inventory=inventory,
        catalog={
            bundle.sku: bundle,
        },
    )

    service.mark_as_paid(
        order=order,
        transaction_reference="PAY-BUNDLE-001",
        amount=Decimal("360"),
    )

    shipment = service.ship_order(
        order=order,
        inventory=inventory,
        timestamp=datetime(
            2026,
            9,
            28,
            10,
            0,
        ),
    )

    assert order.status == OrderStatus.SHIPPED
    assert shipment.order_id == order.order_id

    assert inventory.get_physical_stock(
        "BOOK-001"
    ) == 8

    assert inventory.get_physical_stock(
        "USB-001"
    ) == 6

    assert inventory.get_reserved_stock(
        "BOOK-001"
    ) == 0

    assert inventory.get_reserved_stock(
        "USB-001"
    ) == 0


def test_cancel_bundle_order_releases_all_component_reservations():
    inventory, book, flash_drive = create_inventory()

    bundle = create_bundle(
        book,
        flash_drive,
    )

    order = create_order(
        quantity=2
    )

    service = OrderService()

    service.reserve_order(
        order=order,
        inventory=inventory,
        catalog={
            bundle.sku: bundle,
        },
    )

    assert inventory.get_available_stock(
        "BOOK-001"
    ) == 8

    assert inventory.get_available_stock(
        "USB-001"
    ) == 6

    service.cancel_order(
        order=order,
        inventory=inventory,
    )

    assert order.status == OrderStatus.CANCELLED

    assert inventory.get_reserved_stock(
        "BOOK-001"
    ) == 0

    assert inventory.get_reserved_stock(
        "USB-001"
    ) == 0

    assert inventory.get_available_stock(
        "BOOK-001"
    ) == 10

    assert inventory.get_available_stock(
        "USB-001"
    ) == 10