import pytest

from app.domain.enums.warehouse_type import WarehouseType
from app.domain.models.inventory import Inventory
from app.domain.models.inventory_ledger import InventoryLedger
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.domain.models.sales_rule_context import SalesRuleContext
from app.domain.models.warehouse import Warehouse
from app.services.inventory_service import InventoryService
from app.services.order_service import OrderService
from app.services.sales_rule_engine import SalesRuleEngine
from app.strategies.sales_rules.sales_rule import SalesRule


class RejectOrderRule(SalesRule):
    def validate(self, context: SalesRuleContext) -> None:
        raise ValueError("Order rejected by sales rule")


class CaptureContextRule(SalesRule):
    def __init__(self):
        self.context = None

    def validate(self, context: SalesRuleContext) -> None:
        self.context = context


def create_order_service(rule):
    engine = SalesRuleEngine(
        rules=[rule],
    )

    inventory_service = InventoryService(
        InventoryLedger(),
    )

    return OrderService(
        inventory_service=inventory_service,
        sales_rule_engine=engine,
    )


def create_order():
    item = OrderItem(
        item_id="ITEM-001",
        sku="BOOK-001",
        quantity=1,
    )

    order = Order(
        order_id="ORD-001",
    )
    order.add_item(item)

    return order


def create_inventory():
    warehouse = Warehouse(
        warehouse_id="WH-001",
        name="Central Warehouse",
        location="Tehran",
        warehouse_type=WarehouseType.CENTRAL,
    )

    return Inventory(
        warehouse=warehouse,
    )


def test_order_service_runs_sales_rules_before_reservation():
    rule = CaptureContextRule()
    service = create_order_service(rule)

    order = create_order()
    inventory = create_inventory()

    with pytest.raises(
        ValueError,
        match="Insufficient available stock",
    ):
        service.reserve_order(
            order=order,
            inventory=inventory,
        )

    assert rule.context is not None
    assert rule.context.order is order


def test_order_service_stops_when_sales_rule_fails():
    rule = RejectOrderRule()
    service = create_order_service(rule)

    order = create_order()
    inventory = create_inventory()

    with pytest.raises(
        ValueError,
        match="Order rejected by sales rule",
    ):
        service.reserve_order(
            order=order,
            inventory=inventory,
        )

    assert order.status.value == "created"