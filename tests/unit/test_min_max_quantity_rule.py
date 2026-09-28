import pytest

from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.domain.models.sales_rule_context import SalesRuleContext
from app.strategies.sales_rules.min_max_quantity_rule import (
    MinMaxQuantityRule,
)


def create_context(
    sku: str,
    quantity: int,
) -> SalesRuleContext:
    order = Order(
        order_id="ORD-001",
    )

    order.add_item(
        OrderItem(
            item_id="ITEM-001",
            sku=sku,
            quantity=quantity,
        )
    )

    return SalesRuleContext(
        order=order,
    )


def test_min_max_quantity_rule_allows_quantity_inside_range():
    rule = MinMaxQuantityRule(
        limits={
            "LAPTOP-001": (2, 10),
        }
    )

    rule.validate(
        create_context(
            sku="LAPTOP-001",
            quantity=5,
        )
    )


def test_min_max_quantity_rule_allows_minimum_quantity():
    rule = MinMaxQuantityRule(
        limits={
            "LAPTOP-001": (2, 10),
        }
    )

    rule.validate(
        create_context(
            sku="LAPTOP-001",
            quantity=2,
        )
    )


def test_min_max_quantity_rule_allows_maximum_quantity():
    rule = MinMaxQuantityRule(
        limits={
            "LAPTOP-001": (2, 10),
        }
    )

    rule.validate(
        create_context(
            sku="LAPTOP-001",
            quantity=10,
        )
    )


def test_min_max_quantity_rule_rejects_quantity_below_minimum():
    rule = MinMaxQuantityRule(
        limits={
            "LAPTOP-001": (2, 10),
        }
    )

    with pytest.raises(
        ValueError,
        match="Minimum quantity for SKU LAPTOP-001 is 2",
    ):
        rule.validate(
            create_context(
                sku="LAPTOP-001",
                quantity=1,
            )
        )


def test_min_max_quantity_rule_rejects_quantity_above_maximum():
    rule = MinMaxQuantityRule(
        limits={
            "LAPTOP-001": (2, 10),
        }
    )

    with pytest.raises(
        ValueError,
        match="Maximum quantity for SKU LAPTOP-001 is 10",
    ):
        rule.validate(
            create_context(
                sku="LAPTOP-001",
                quantity=11,
            )
        )


def test_min_max_quantity_rule_allows_unlimited_maximum():
    rule = MinMaxQuantityRule(
        limits={
            "LAPTOP-001": (2, None),
        }
    )

    rule.validate(
        create_context(
            sku="LAPTOP-001",
            quantity=100,
        )
    )


def test_min_max_quantity_rule_ignores_unconfigured_sku():
    rule = MinMaxQuantityRule(
        limits={
            "LAPTOP-001": (2, 10),
        }
    )

    rule.validate(
        create_context(
            sku="PHONE-001",
            quantity=100,
        )
    )


def test_min_max_quantity_rule_supports_multiple_skus():
    rule = MinMaxQuantityRule(
        limits={
            "LAPTOP-001": (1, 5),
            "PHONE-001": (2, 10),
        }
    )

    order_context = SalesRuleContext(
        order=Order(
            order_id="ORD-001",
        )
    )

    order_context.order.add_item(
        OrderItem(
            item_id="ITEM-001",
            sku="LAPTOP-001",
            quantity=3,
        )
    )

    order_context.order.add_item(
        OrderItem(
            item_id="ITEM-002",
            sku="PHONE-001",
            quantity=5,
        )
    )

    rule.validate(order_context)


def test_min_max_quantity_rule_rejects_empty_limits():
    with pytest.raises(
        ValueError,
        match="At least one quantity limit is required",
    ):
        MinMaxQuantityRule(
            limits={}
        )


def test_min_max_quantity_rule_rejects_non_mapping():
    with pytest.raises(
        ValueError,
        match="Limits must be a mapping",
    ):
        MinMaxQuantityRule(
            limits=None
        )


def test_min_max_quantity_rule_rejects_invalid_sku():
    with pytest.raises(
        ValueError,
        match="SKU cannot be empty",
    ):
        MinMaxQuantityRule(
            limits={
                "": (1, 5),
            }
        )


def test_min_max_quantity_rule_rejects_invalid_limit_shape():
    with pytest.raises(
        ValueError,
        match="Quantity limit must be a tuple",
    ):
        MinMaxQuantityRule(
            limits={
                "LAPTOP-001": (1,),
            }
        )


def test_min_max_quantity_rule_rejects_zero_minimum():
    with pytest.raises(
        ValueError,
        match="Minimum quantity must be positive",
    ):
        MinMaxQuantityRule(
            limits={
                "LAPTOP-001": (0, 5),
            }
        )


def test_min_max_quantity_rule_rejects_negative_minimum():
    with pytest.raises(
        ValueError,
        match="Minimum quantity must be positive",
    ):
        MinMaxQuantityRule(
            limits={
                "LAPTOP-001": (-1, 5),
            }
        )


def test_min_max_quantity_rule_rejects_zero_maximum():
    with pytest.raises(
        ValueError,
        match="Maximum quantity must be positive",
    ):
        MinMaxQuantityRule(
            limits={
                "LAPTOP-001": (1, 0),
            }
        )


def test_min_max_quantity_rule_rejects_maximum_below_minimum():
    with pytest.raises(
        ValueError,
        match="Maximum quantity cannot be lower",
    ):
        MinMaxQuantityRule(
            limits={
                "LAPTOP-001": (10, 5),
            }
        )


def test_min_max_quantity_rule_rejects_boolean_minimum():
    with pytest.raises(
        ValueError,
        match="Minimum quantity must be an integer",
    ):
        MinMaxQuantityRule(
            limits={
                "LAPTOP-001": (True, 5),
            }
        )


def test_min_max_quantity_rule_rejects_boolean_maximum():
    with pytest.raises(
        ValueError,
        match="Maximum quantity must be an integer",
    ):
        MinMaxQuantityRule(
            limits={
                "LAPTOP-001": (1, True),
            }
        )