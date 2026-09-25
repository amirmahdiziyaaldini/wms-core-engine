from decimal import Decimal

import pytest

from app.domain.models.base_product import BaseProduct
from app.strategies.pricing.tiered_pricing_strategy import (
    PriceTier,
    TieredPricingStrategy,
)


def create_product(price=Decimal("100")):
    return BaseProduct(
        sku="BOOK-001",
        name="Python Book",
        barcode="123456789",
        category="Books",
        base_price=price,
    )


def test_quantity_1_uses_base_price():
    strategy = TieredPricingStrategy()

    price = strategy.calculate_unit_price(
        product=create_product(),
        quantity=1,
    )

    assert price == Decimal("100")


def test_quantity_5_uses_base_price():
    strategy = TieredPricingStrategy()

    price = strategy.calculate_unit_price(
        product=create_product(),
        quantity=5,
    )

    assert price == Decimal("100")


def test_quantity_6_gets_ten_percent_discount():
    strategy = TieredPricingStrategy()

    price = strategy.calculate_unit_price(
        product=create_product(),
        quantity=6,
    )

    assert price == Decimal("90")


def test_quantity_20_gets_ten_percent_discount():
    strategy = TieredPricingStrategy()

    price = strategy.calculate_unit_price(
        product=create_product(),
        quantity=20,
    )

    assert price == Decimal("90")


def test_quantity_21_gets_twenty_percent_discount():
    strategy = TieredPricingStrategy()

    price = strategy.calculate_unit_price(
        product=create_product(),
        quantity=21,
    )

    assert price == Decimal("80")


def test_quantity_25_calculates_expected_unit_price():
    strategy = TieredPricingStrategy()

    price = strategy.calculate_unit_price(
        product=create_product(),
        quantity=25,
    )

    assert price == Decimal("80")


def test_quantity_25_total_is_2000():
    strategy = TieredPricingStrategy()

    unit_price = strategy.calculate_unit_price(
        product=create_product(),
        quantity=25,
    )

    total = unit_price * 25

    assert unit_price == Decimal("80")
    assert total == Decimal("2000")


def test_quantity_10_calculates_expected_total():
    strategy = TieredPricingStrategy()

    unit_price = strategy.calculate_unit_price(
        product=create_product(),
        quantity=10,
    )

    total = unit_price * 10

    assert unit_price == Decimal("90")
    assert total == Decimal("900")


def test_zero_quantity_is_rejected():
    strategy = TieredPricingStrategy()

    with pytest.raises(
        ValueError,
        match="Quantity must be positive",
    ):
        strategy.calculate_unit_price(
            product=create_product(),
            quantity=0,
        )


def test_negative_quantity_is_rejected():
    strategy = TieredPricingStrategy()

    with pytest.raises(
        ValueError,
        match="Quantity must be positive",
    ):
        strategy.calculate_unit_price(
            product=create_product(),
            quantity=-1,
        )


def test_custom_tiers_cannot_have_gap():
    with pytest.raises(
        ValueError,
        match="gaps or overlaps",
    ):
        TieredPricingStrategy(
            tiers=[
                PriceTier(
                    min_quantity=1,
                    max_quantity=5,
                    discount_rate=Decimal("0"),
                ),
                PriceTier(
                    min_quantity=7,
                    max_quantity=None,
                    discount_rate=Decimal("0.20"),
                ),
            ]
        )


def test_custom_tiers_cannot_overlap():
    with pytest.raises(
        ValueError,
        match="gaps or overlaps",
    ):
        TieredPricingStrategy(
            tiers=[
                PriceTier(
                    min_quantity=1,
                    max_quantity=10,
                    discount_rate=Decimal("0"),
                ),
                PriceTier(
                    min_quantity=10,
                    max_quantity=None,
                    discount_rate=Decimal("0.20"),
                ),
            ]
        )


def test_first_tier_must_start_at_one():
    with pytest.raises(
        ValueError,
        match="first tier must start",
    ):
        TieredPricingStrategy(
            tiers=[
                PriceTier(
                    min_quantity=2,
                    max_quantity=None,
                    discount_rate=Decimal("0"),
                ),
            ]
        )


def test_open_ended_tier_must_be_last():
    with pytest.raises(
        ValueError,
        match="open-ended tier must be the last",
    ):
        TieredPricingStrategy(
            tiers=[
                PriceTier(
                    min_quantity=1,
                    max_quantity=None,
                    discount_rate=Decimal("0"),
                ),
                PriceTier(
                    min_quantity=2,
                    max_quantity=5,
                    discount_rate=Decimal("0.10"),
                ),
            ]
        )


def test_negative_discount_is_rejected():
    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        TieredPricingStrategy(
            tiers=[
                PriceTier(
                    min_quantity=1,
                    max_quantity=None,
                    discount_rate=Decimal("-0.10"),
                ),
            ]
        )


def test_discount_above_one_is_rejected():
    with pytest.raises(
        ValueError,
        match="cannot exceed 1",
    ):
        TieredPricingStrategy(
            tiers=[
                PriceTier(
                    min_quantity=1,
                    max_quantity=None,
                    discount_rate=Decimal("1.10"),
                ),
            ]
        )