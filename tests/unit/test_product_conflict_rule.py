import pytest

from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.domain.models.sales_rule_context import SalesRuleContext
from app.strategies.sales_rules.product_conflict_rule import ProductConflictRule


def create_order(skus):
    order = Order(
        order_id="ORD-001",
    )

    for index, sku in enumerate(skus, start=1):
        order.add_item(
            OrderItem(
                item_id=f"ITEM-{index:03d}",
                sku=sku,
                quantity=1,
            )
        )

    return order


def create_context(skus):
    return SalesRuleContext(
        order=create_order(skus),
    )


def test_product_conflict_rule_rejects_conflicting_products():
    rule = ProductConflictRule(
        conflicts=[
            {"BOOK-001", "DIGITAL-001"},
        ]
    )

    with pytest.raises(
        ValueError,
        match="Conflicting SKUs in order: BOOK-001, DIGITAL-001",
    ):
        rule.validate(
            create_context(
                ["BOOK-001", "DIGITAL-001"]
            )
        )


def test_product_conflict_rule_is_independent_of_order_item_order():
    rule = ProductConflictRule(
        conflicts=[
            {"BOOK-001", "DIGITAL-001"},
        ]
    )

    with pytest.raises(
        ValueError,
        match="Conflicting SKUs in order: BOOK-001, DIGITAL-001",
    ):
        rule.validate(
            create_context(
                ["DIGITAL-001", "BOOK-001"]
            )
        )


def test_product_conflict_rule_supports_multiple_conflicts():
    rule = ProductConflictRule(
        conflicts=[
            {"BOOK-001", "DIGITAL-001"},
            {"LAPTOP-001", "MOUSE-001"},
        ]
    )

    with pytest.raises(
        ValueError,
        match="Conflicting SKUs in order: LAPTOP-001, MOUSE-001",
    ):
        rule.validate(
            create_context(
                ["LAPTOP-001", "MOUSE-001"]
            )
        )


def test_product_conflict_rule_supports_multiple_sku_conflicts():
    rule = ProductConflictRule(
        conflicts=[
            {
                "LAPTOP-001",
                "MOUSE-001",
                "KEYBOARD-001",
            },
        ]
    )

    with pytest.raises(
        ValueError,
        match=(
            "Conflicting SKUs in order: "
            "KEYBOARD-001, LAPTOP-001, MOUSE-001"
        ),
    ):
        rule.validate(
            create_context(
                [
                    "MOUSE-001",
                    "KEYBOARD-001",
                    "LAPTOP-001",
                ]
            )
        )


def test_product_conflict_rule_allows_non_conflicting_products():
    rule = ProductConflictRule(
        conflicts=[
            {"BOOK-001", "DIGITAL-001"},
        ]
    )

    rule.validate(
        create_context(
            ["BOOK-001", "PEN-001"]
        )
    )


def test_product_conflict_rule_does_not_require_all_conflicts():
    rule = ProductConflictRule(
        conflicts=[
            {
                "LAPTOP-001",
                "MOUSE-001",
                "KEYBOARD-001",
            },
        ]
    )

    rule.validate(
        create_context(
            ["LAPTOP-001", "MOUSE-001"]
        )
    )


def test_product_conflict_rule_rejects_invalid_conflict():
    with pytest.raises(
        ValueError,
        match="Each conflict must contain at least two SKUs",
    ):
        ProductConflictRule(
            conflicts=[
                {"BOOK-001"},
            ]
        )


def test_product_conflict_rule_rejects_empty_sku():
    with pytest.raises(
        ValueError,
        match="Conflict SKU cannot be empty",
    ):
        ProductConflictRule(
            conflicts=[
                {"BOOK-001", ""},
            ]
        )


def test_product_conflict_rule_removes_duplicate_conflicts():
    rule = ProductConflictRule(
        conflicts=[
            {"BOOK-001", "DIGITAL-001"},
            {"DIGITAL-001", "BOOK-001"},
        ]
    )

    assert len(rule.conflicts) == 1