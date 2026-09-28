from datetime import date
from decimal import Decimal

import pytest

from app.domain.enums.warehouse_type import WarehouseType
from app.domain.models.base_product import BaseProduct
from app.domain.models.batch import Batch
from app.domain.models.inventory import Inventory
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.domain.models.sales_rule_context import SalesRuleContext
from app.domain.models.warehouse import Warehouse
from app.services.order_service import OrderService
from app.services.sales_rule_engine import SalesRuleEngine
from app.strategies.sales_rules.min_max_quantity_rule import (
    MinMaxQuantityRule,
)
from app.strategies.sales_rules.prerequisite_rule import (
    PrerequisiteRule,
)
from app.strategies.sales_rules.product_conflict_rule import (
    ProductConflictRule,
)


def create_order(
    order_id: str,
    items: list[tuple[str, int]],
) -> Order:
    order = Order(
        order_id=order_id,
    )

    for index, (sku, quantity) in enumerate(
        items,
        start=1,
    ):
        order.add_item(
            OrderItem(
                item_id=f"ITEM-{index:03d}",
                sku=sku,
                quantity=quantity,
            )
        )

    return order


def create_inventory(
    product: BaseProduct,
    quantity: int = 20,
) -> Inventory:
    warehouse = Warehouse(
        warehouse_id="WH-001",
        name="Main Warehouse",
        location="Berlin",
        warehouse_type=WarehouseType.CENTRAL,
    )

    inventory = Inventory(
        warehouse=warehouse,
    )

    inventory.add_batch(
        Batch(
            batch_id="BATCH-001",
            product=product,
            quantity=quantity,
            entry_date=date(
                2026,
                1,
                1,
            ),
        )
    )

    return inventory


def test_phase_3_engine_executes_multiple_rules_in_order():
    engine = SalesRuleEngine(
        rules=[
            MinMaxQuantityRule(
                limits={
                    "BOOK-001": (1, 5),
                }
            ),
            ProductConflictRule(
                conflicts=[
                    {
                        "BOOK-001",
                        "DIGITAL-001",
                    }
                ]
            ),
            PrerequisiteRule(
                required_sku="PARENT-001",
                child_skus=[
                    "ACCESSORY-001",
                ],
                mode="any",
            ),
        ]
    )

    context = SalesRuleContext(
        order=create_order(
            "ORD-001",
            [
                ("BOOK-001", 2),
            ],
        )
    )

    engine.validate(context)


def test_phase_3_rule_failure_stops_following_rules():
    engine = SalesRuleEngine(
        rules=[
            MinMaxQuantityRule(
                limits={
                    "BOOK-001": (1, 2),
                }
            ),
            ProductConflictRule(
                conflicts=[
                    {
                        "BOOK-001",
                        "DIGITAL-001",
                    }
                ]
            ),
        ]
    )

    context = SalesRuleContext(
        order=create_order(
            "ORD-001",
            [
                ("BOOK-001", 3),
            ],
        )
    )

    with pytest.raises(
        ValueError,
        match="Maximum quantity for SKU BOOK-001 is 2",
    ):
        engine.validate(context)


def test_phase_3_conflict_rule_runs_before_inventory_reservation():
    product = BaseProduct(
        sku="BOOK-001",
        name="Book",
        barcode="1001",
        category="Books",
        base_price=Decimal("100"),
    )

    inventory = create_inventory(
        product=product,
        quantity=10,
    )

    engine = SalesRuleEngine(
        rules=[
            ProductConflictRule(
                conflicts=[
                    {
                        "BOOK-001",
                        "DIGITAL-001",
                    }
                ]
            )
        ]
    )

    service = OrderService(
        sales_rule_engine=engine,
    )

    order = create_order(
        "ORD-001",
        [
            ("BOOK-001", 1),
            ("DIGITAL-001", 1),
        ],
    )

    with pytest.raises(
        ValueError,
        match="Conflicting SKUs in order",
    ):
        service.reserve_order(
            order=order,
            inventory=inventory,
        )

    assert inventory.get_reserved_stock(
        "BOOK-001"
    ) == 0

    assert inventory.get_available_stock(
        "BOOK-001"
    ) == 10


def test_phase_3_min_max_rule_runs_before_inventory_reservation():
    product = BaseProduct(
        sku="BOOK-001",
        name="Book",
        barcode="1001",
        category="Books",
        base_price=Decimal("100"),
    )

    inventory = create_inventory(
        product=product,
        quantity=10,
    )

    engine = SalesRuleEngine(
        rules=[
            MinMaxQuantityRule(
                limits={
                    "BOOK-001": (1, 2),
                }
            )
        ]
    )

    service = OrderService(
        sales_rule_engine=engine,
    )

    order = create_order(
        "ORD-001",
        [
            ("BOOK-001", 3),
        ],
    )

    with pytest.raises(
        ValueError,
        match="Maximum quantity for SKU BOOK-001 is 2",
    ):
        service.reserve_order(
            order=order,
            inventory=inventory,
        )

    assert inventory.get_reserved_stock(
        "BOOK-001"
    ) == 0

    assert inventory.get_available_stock(
        "BOOK-001"
    ) == 10


def test_phase_3_prerequisite_rule_runs_before_inventory_reservation():
    product = BaseProduct(
        sku="ACCESSORY-001",
        name="Accessory",
        barcode="1002",
        category="Accessories",
        base_price=Decimal("50"),
    )

    inventory = create_inventory(
        product=product,
        quantity=10,
    )

    engine = SalesRuleEngine(
        rules=[
            PrerequisiteRule(
                required_sku="PARENT-001",
                child_skus=[
                    "ACCESSORY-001",
                ],
                mode="any",
            )
        ]
    )

    service = OrderService(
        sales_rule_engine=engine,
    )

    order = create_order(
        "ORD-001",
        [
            ("ACCESSORY-001", 1),
        ],
    )

    with pytest.raises(
        ValueError,
        match="Prerequisite SKU 'PARENT-001' is required",
    ):
        service.reserve_order(
            order=order,
            inventory=inventory,
        )

    assert inventory.get_reserved_stock(
        "ACCESSORY-001"
    ) == 0

    assert inventory.get_available_stock(
        "ACCESSORY-001"
    ) == 10


def test_phase_3_successful_rules_are_followed_by_pricing_and_reservation():
    product = BaseProduct(
        sku="BOOK-001",
        name="Book",
        barcode="1001",
        category="Books",
        base_price=Decimal("100"),
    )

    inventory = create_inventory(
        product=product,
        quantity=20,
    )

    engine = SalesRuleEngine(
        rules=[
            MinMaxQuantityRule(
                limits={
                    "BOOK-001": (1, 10),
                }
            )
        ]
    )

    service = OrderService(
        sales_rule_engine=engine,
    )

    order = create_order(
        "ORD-001",
        [
            ("BOOK-001", 6),
        ],
    )

    reservations = service.reserve_order(
        order=order,
        inventory=inventory,
        catalog={
            "BOOK-001": product,
        },
    )

    assert len(reservations) == 1

    assert order.items[0].unit_price == Decimal("90")

    assert order.items[0].line_total == Decimal("540")

    assert order.total_amount == Decimal("540")

    assert inventory.get_reserved_stock(
        "BOOK-001"
    ) == 6

    assert inventory.get_available_stock(
        "BOOK-001"
    ) == 14