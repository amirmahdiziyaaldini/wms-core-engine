import pytest
from decimal import Decimal

from app.domain.models.perishable_product import PerishableProduct


def create_perishable_product():
    return PerishableProduct(
        sku="MILK-001",
        name="Fresh Milk",
        barcode="123456789",
        category="Food",
        base_price=Decimal("50000"),
    )


def test_create_perishable_product():
    product = create_perishable_product()

    assert product.sku == "MILK-001"
    assert product.name == "Fresh Milk"
    assert product.barcode == "123456789"
    assert product.category == "Food"
    assert product.base_price == Decimal("50000")


def test_expiry_tracking_is_enabled():
    product = create_perishable_product()

    assert product.expiry_tracking is True


def test_perishable_product_price_get():
    product = create_perishable_product()

    assert product.price_get() == Decimal("50000")


def test_perishable_product_get_price():
    product = create_perishable_product()

    assert product.get_price() == Decimal("50000")


def test_perishable_product_price_methods_match():
    product = create_perishable_product()

    assert product.price_get() == product.get_price()


def test_perishable_product_accepts_zero_price():
    product = PerishableProduct(
        sku="MILK-001",
        name="Free Milk",
        barcode="123456789",
        category="Food",
        base_price=Decimal("0"),
    )

    assert product.price_get() == Decimal("0")


def test_perishable_product_rejects_negative_price():
    with pytest.raises(ValueError):
        PerishableProduct(
            sku="MILK-001",
            name="Fresh Milk",
            barcode="123456789",
            category="Food",
            base_price=Decimal("-1"),
        )


def test_perishable_product_rejects_non_decimal_price():
    with pytest.raises(ValueError):
        PerishableProduct(
            sku="MILK-001",
            name="Fresh Milk",
            barcode="123456789",
            category="Food",
            base_price=50000,
        )


def test_perishable_product_requires_valid_sku():
    with pytest.raises(ValueError):
        PerishableProduct(
            sku="",
            name="Fresh Milk",
            barcode="123456789",
            category="Food",
            base_price=Decimal("50000"),
        )


def test_perishable_product_requires_valid_name():
    with pytest.raises(ValueError):
        PerishableProduct(
            sku="MILK-001",
            name="",
            barcode="123456789",
            category="Food",
            base_price=Decimal("50000"),
        )