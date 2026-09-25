import pytest

from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.domain.models.sales_rule_context import SalesRuleContext
from app.strategies.sales_rules.sales_rule import SalesRule
from app.services.sales_rule_engine import SalesRuleEngine


class PassingRule(SalesRule):
    def __init__(self):
        self.called = False

    def validate(self, context: SalesRuleContext) -> None:
        self.called = True


class FailingRule(SalesRule):
    def __init__(self):
        self.called = False

    def validate(self, context: SalesRuleContext) -> None:
        self.called = True
        raise ValueError("Sales rule validation failed")


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


def create_context():
    return SalesRuleContext(
        order=create_order(),
    )


def test_sales_rule_engine_runs_rules_in_order():
    first_rule = PassingRule()
    second_rule = PassingRule()

    engine = SalesRuleEngine(
        rules=[
            first_rule,
            second_rule,
        ]
    )

    engine.validate(create_context())

    assert first_rule.called is True
    assert second_rule.called is True


def test_sales_rule_engine_stops_when_rule_fails():
    first_rule = FailingRule()
    second_rule = PassingRule()

    engine = SalesRuleEngine(
        rules=[
            first_rule,
            second_rule,
        ]
    )

    with pytest.raises(
        ValueError,
        match="Sales rule validation failed",
    ):
        engine.validate(create_context())

    assert first_rule.called is True
    assert second_rule.called is False


def test_sales_rule_engine_accepts_rule_after_initialization():
    rule = PassingRule()
    engine = SalesRuleEngine()

    engine.add_rule(rule)
    engine.validate(create_context())

    assert rule.called is True


def test_sales_rule_engine_rejects_invalid_rule():
    engine = SalesRuleEngine()

    with pytest.raises(
        ValueError,
        match="Rule must be a SalesRule",
    ):
        engine.add_rule(object())


def test_sales_rule_engine_rejects_invalid_context():
    engine = SalesRuleEngine()

    with pytest.raises(
        ValueError,
        match="Context must be a SalesRuleContext",
    ):
        engine.validate(object())


def test_sales_rule_context_requires_order():
    with pytest.raises(
        ValueError,
        match="Order must be an Order",
    ):
        SalesRuleContext(order=object())