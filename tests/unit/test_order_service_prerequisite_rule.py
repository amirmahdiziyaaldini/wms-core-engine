import pytest

from app.domain.enums.warehouse_type import WarehouseType
from app.domain.models.inventory import Inventory
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.domain.models.warehouse import Warehouse
from app.services.order_service import OrderService
from app.services.sales_rule_engine import SalesRuleEngine
from app.strategies.sales_rules.prerequisite_rule import PrerequisiteRule


def create_inventory():
    warehouse = Warehouse(
        warehouse_id="WH-001",
        name="Main Warehouse",
        location="Berlin",
        warehouse_type=WarehouseType.CENTRAL,
    )

    return Inventory(warehouse)


def create_order(*skus):
    order = Order("ORD-1001")

    for index, sku in enumerate(skus, start=1):
        order.add_item(
            OrderItem(
                item_id=f"ITEM-{index}",
                sku=sku,
                quantity=1,
            )
        )

    return order


def create_service(rule):
    engine = SalesRuleEngine([rule])

    return OrderService(
        sales_rule_engine=engine,
    )


def test_prerequisite_rule_is_executed_before_inventory_validation():
    rule = PrerequisiteRule(
        required_sku="PARENT-001",
        child_skus=["CHILD-001"],
        mode="any",
    )

    service = create_service(rule)
    order = create_order("CHILD-001")
    inventory = create_inventory()

    with pytest.raises(
        ValueError,
        match="Prerequisite SKU 'PARENT-001' is required",
    ):
        service.reserve_order(
            order=order,
            inventory=inventory,
        )


def test_prerequisite_rule_allows_order_with_required_product():
    rule = PrerequisiteRule(
        required_sku="PARENT-001",
        child_skus=["CHILD-001"],
        mode="any",
    )

    service = create_service(rule)

    order = create_order(
        "PARENT-001",
        "CHILD-001",
    )

    inventory = create_inventory()

    with pytest.raises(
        ValueError,
        match="Insufficient available stock",
    ):
        service.reserve_order(
            order=order,
            inventory=inventory,
        )


def test_prerequisite_rule_any_mode_rejects_order():
    rule = PrerequisiteRule(
        required_sku="PARENT-001",
        child_skus=[
            "CHILD-001",
            "CHILD-002",
        ],
        mode="any",
    )

    service = create_service(rule)
    order = create_order("CHILD-002")
    inventory = create_inventory()

    with pytest.raises(
        ValueError,
        match="Prerequisite SKU 'PARENT-001' is required",
    ):
        service.reserve_order(
            order=order,
            inventory=inventory,
        )


def test_prerequisite_rule_all_mode_rejects_order():
    rule = PrerequisiteRule(
        required_sku="PARENT-001",
        child_skus=[
            "CHILD-001",
            "CHILD-002",
        ],
        mode="all",
    )

    service = create_service(rule)

    order = create_order(
        "CHILD-001",
        "CHILD-002",
    )

    inventory = create_inventory()

    with pytest.raises(
        ValueError,
        match="Prerequisite SKU 'PARENT-001' is required",
    ):
        service.reserve_order(
            order=order,
            inventory=inventory,
        )