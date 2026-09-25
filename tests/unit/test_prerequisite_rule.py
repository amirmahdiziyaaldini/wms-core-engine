import pytest

from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.domain.models.sales_rule_context import SalesRuleContext
from app.strategies.sales_rules.prerequisite_rule import PrerequisiteRule


def create_context(*skus):
    order = Order("ORD-1001")

    for index, sku in enumerate(skus, start=1):
        order.add_item(
            OrderItem(
                item_id=f"ITEM-{index}",
                sku=sku,
                quantity=1,
            )
        )

    return SalesRuleContext(order)


def test_any_mode_passes_when_one_child_exists_with_required_product():
    rule = PrerequisiteRule(
        required_sku="PARENT-001",
        child_skus=["CHILD-001", "CHILD-002"],
        mode="any",
    )

    context = create_context(
        "PARENT-001",
        "CHILD-001",
    )

    rule.validate(context)


def test_any_mode_passes_when_no_child_exists():
    rule = PrerequisiteRule(
        required_sku="PARENT-001",
        child_skus=["CHILD-001", "CHILD-002"],
        mode="any",
    )

    context = create_context("OTHER-001")

    rule.validate(context)


def test_any_mode_fails_when_child_exists_without_required_product():
    rule = PrerequisiteRule(
        required_sku="PARENT-001",
        child_skus=["CHILD-001", "CHILD-002"],
        mode="any",
    )

    context = create_context("CHILD-002")

    with pytest.raises(
        ValueError,
        match="Prerequisite SKU 'PARENT-001' is required",
    ):
        rule.validate(context)


def test_all_mode_passes_when_all_children_and_required_product_exist():
    rule = PrerequisiteRule(
        required_sku="PARENT-001",
        child_skus=["CHILD-001", "CHILD-002"],
        mode="all",
    )

    context = create_context(
        "PARENT-001",
        "CHILD-001",
        "CHILD-002",
    )

    rule.validate(context)


def test_all_mode_passes_when_only_some_children_exist():
    rule = PrerequisiteRule(
        required_sku="PARENT-001",
        child_skus=["CHILD-001", "CHILD-002"],
        mode="all",
    )

    context = create_context(
        "PARENT-001",
        "CHILD-001",
    )

    rule.validate(context)


def test_all_mode_fails_when_all_children_exist_without_required_product():
    rule = PrerequisiteRule(
        required_sku="PARENT-001",
        child_skus=["CHILD-001", "CHILD-002"],
        mode="all",
    )

    context = create_context(
        "CHILD-001",
        "CHILD-002",
    )

    with pytest.raises(
        ValueError,
        match="Prerequisite SKU 'PARENT-001' is required",
    ):
        rule.validate(context)


def test_rule_accepts_single_child_sku():
    rule = PrerequisiteRule(
        required_sku="PARENT-001",
        child_skus=["CHILD-001"],
    )

    context = create_context("CHILD-001")

    with pytest.raises(
        ValueError,
        match="Prerequisite SKU 'PARENT-001' is required",
    ):
        rule.validate(context)


def test_rule_rejects_empty_child_skus():
    with pytest.raises(
        ValueError,
        match="At least one child SKU is required",
    ):
        PrerequisiteRule(
            required_sku="PARENT-001",
            child_skus=[],
        )


def test_rule_rejects_invalid_mode():
    with pytest.raises(
        ValueError,
        match="Mode must be either 'any' or 'all'",
    ):
        PrerequisiteRule(
            required_sku="PARENT-001",
            child_skus=["CHILD-001"],
            mode="invalid",
        )


def test_rule_rejects_empty_required_sku():
    with pytest.raises(
        ValueError,
        match="Required SKU cannot be empty",
    ):
        PrerequisiteRule(
            required_sku="",
            child_skus=["CHILD-001"],
        )


def test_rule_rejects_empty_child_sku():
    with pytest.raises(
        ValueError,
        match="Child SKU cannot be empty",
    ):
        PrerequisiteRule(
            required_sku="PARENT-001",
            child_skus=[""],
        )


def test_rule_removes_duplicate_child_skus():
    rule = PrerequisiteRule(
        required_sku="PARENT-001",
        child_skus=[
            "CHILD-001",
            "CHILD-001",
            "CHILD-002",
        ],
    )

    assert rule.child_skus == [
        "CHILD-001",
        "CHILD-002",
    ]