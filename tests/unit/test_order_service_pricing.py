from decimal import Decimal
from datetime import date

import pytest

from app.domain.enums.warehouse_type import WarehouseType
from app.domain.models.base_product import BaseProduct
from app.domain.models.batch import Batch
from app.domain.models.inventory import Inventory
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.domain.models.warehouse import Warehouse
from app.services.order_service import OrderService
from app.services.pricing_service import PricingService
from app.services.sales_rule_engine import SalesRuleEngine
from app.strategies.sales_rules.sales_rule import SalesRule


class RejectOrderRule(SalesRule):
    def validate(self, context):
        raise ValueError("Order rejected by rule")


def create_product(
    sku: str,
    price: str,
) -> BaseProduct:
    return BaseProduct(
        sku=sku,
        name=f"Product {sku}",
        barcode=f"BAR-{sku}",
        category="Test",
        base_price=Decimal(price),
    )


def create_inventory(
    sku: str,
    quantity: int,
) -> Inventory:
    warehouse = Warehouse(
        warehouse_id="WH-001",
        name="Main Warehouse",
        location="Tehran",
        warehouse_type=WarehouseType.CENTRAL,
    )

    inventory = Inventory(
        warehouse=warehouse,
    )

    if quantity > 0:
        inventory.add_batch(
            Batch(
                batch_id=f"BATCH-{sku}",
                product=create_product(sku, "100"),
                quantity=quantity,
                entry_date=date(2026, 1, 1),
            )
        )

    return inventory


def create_order(
    order_id: str = "ORD-001",
    sku: str = "SKU-001",
    quantity: int = 1,
) -> Order:
    order = Order(
        order_id=order_id,
    )

    order.add_item(
        OrderItem(
            item_id=f"ITEM-{order_id}",
            sku=sku,
            quantity=quantity,
        )
    )

    return order


def test_order_service_accepts_pricing_service_dependency():
    pricing_service = PricingService()

    service = OrderService(
        pricing_service=pricing_service,
    )

    assert service.pricing_service is pricing_service


def test_validation_rules_run_before_pricing():
    order = create_order()
    inventory = create_inventory(
        sku="SKU-001",
        quantity=10,
    )

    pricing_service = PricingService()

    service = OrderService(
        sales_rule_engine=SalesRuleEngine(
            rules=[RejectOrderRule()]
        ),
        pricing_service=pricing_service,
    )

    catalog = {
        "SKU-001": create_product(
            sku="SKU-001",
            price="100",
        )
    }

    with pytest.raises(
        ValueError,
        match="Order rejected by rule",
    ):
        service.reserve_order(
            order=order,
            inventory=inventory,
            catalog=catalog,
        )

    assert order.items[0].unit_price is None
    assert order.items[0].line_total is None
    assert order.total is None
    assert inventory.reservations == {}


def test_pricing_runs_after_validation_and_before_reservation():
    order = create_order(
        quantity=6,
    )

    inventory = create_inventory(
        sku="SKU-001",
        quantity=10,
    )

    catalog = {
        "SKU-001": create_product(
            sku="SKU-001",
            price="100",
        )
    }

    service = OrderService()

    reservations = service.reserve_order(
        order=order,
        inventory=inventory,
        catalog=catalog,
    )

    item = order.items[0]

    assert item.unit_price == Decimal("90")
    assert item.line_total == Decimal("540")
    assert order.total == Decimal("540")
    assert len(reservations) == 1
    assert len(inventory.reservations) == 1


def test_order_total_is_calculated_from_line_price_snapshots():
    order = Order(
        order_id="ORD-001",
    )

    order.add_item(
        OrderItem(
            item_id="ITEM-001",
            sku="SKU-001",
            quantity=2,
        )
    )

    order.add_item(
        OrderItem(
            item_id="ITEM-002",
            sku="SKU-002",
            quantity=3,
        )
    )

    order.items[0].set_unit_price(
        Decimal("100")
    )

    order.items[1].set_unit_price(
        Decimal("50")
    )

    order.calculate_total()

    assert order.total == Decimal("350")


def test_order_price_snapshot_does_not_change_after_catalog_price_changes():
    order = create_order(
        quantity=6,
    )

    inventory = create_inventory(
        sku="SKU-001",
        quantity=10,
    )

    product = create_product(
        sku="SKU-001",
        price="100",
    )

    catalog = {
        "SKU-001": product,
    }

    service = OrderService()

    service.reserve_order(
        order=order,
        inventory=inventory,
        catalog=catalog,
    )

    assert order.items[0].unit_price == Decimal("90")
    assert order.items[0].line_total == Decimal("540")
    assert order.total == Decimal("540")

    product.base_price = Decimal("1000")

    assert order.items[0].unit_price == Decimal("90")
    assert order.items[0].line_total == Decimal("540")
    assert order.total == Decimal("540")


def test_inventory_failure_does_not_create_reservation():
    order = create_order(
        quantity=10,
    )

    inventory = create_inventory(
        sku="SKU-001",
        quantity=5,
    )

    catalog = {
        "SKU-001": create_product(
            sku="SKU-001",
            price="100",
        )
    }

    service = OrderService()

    with pytest.raises(
        ValueError,
        match="Insufficient available stock",
    ):
        service.reserve_order(
            order=order,
            inventory=inventory,
            catalog=catalog,
        )

    assert inventory.reservations == {}

    assert order.items[0].unit_price == Decimal("90")
    assert order.items[0].line_total == Decimal("900")
    assert order.total == Decimal("900")


def test_multiple_order_items_are_priced_and_totalled():
    order = Order(
        order_id="ORD-001",
    )

    order.add_item(
        OrderItem(
            item_id="ITEM-001",
            sku="SKU-001",
            quantity=6,
        )
    )

    order.add_item(
        OrderItem(
            item_id="ITEM-002",
            sku="SKU-002",
            quantity=2,
        )
    )

    warehouse = Warehouse(
        warehouse_id="WH-001",
        name="Main Warehouse",
        location="Tehran",
        warehouse_type=WarehouseType.CENTRAL,
    )

    inventory = Inventory(
        warehouse=warehouse,
    )

    inventory.add_batch(
        Batch(
            batch_id="BATCH-001",
            product=create_product(
                "SKU-001",
                "100",
            ),
            quantity=10,
            entry_date=date(2026, 1, 1),
        )
    )

    inventory.add_batch(
        Batch(
            batch_id="BATCH-002",
            product=create_product(
                "SKU-002",
                "200",
            ),
            quantity=10,
            entry_date=date(2026, 1, 1),
        )
    )

    catalog = {
        "SKU-001": create_product(
            "SKU-001",
            "100",
        ),
        "SKU-002": create_product(
            "SKU-002",
            "200",
        ),
    }

    service = OrderService()

    service.reserve_order(
        order=order,
        inventory=inventory,
        catalog=catalog,
    )

    assert order.items[0].unit_price == Decimal("90")
    assert order.items[0].line_total == Decimal("540")

    assert order.items[1].unit_price == Decimal("200")
    assert order.items[1].line_total == Decimal("400")

    assert order.total == Decimal("940")