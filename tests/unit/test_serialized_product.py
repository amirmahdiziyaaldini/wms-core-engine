import pytest
from decimal import Decimal

from app.domain.models.serialized_product import SerializedProduct


def create_serialized_product():
    return SerializedProduct(
        sku="LAPTOP-001",
        name="Business Laptop",
        barcode="123456789",
        category="Electronics",
        base_price=Decimal("50000000"),
    )


def test_create_serialized_product():
    product = create_serialized_product()

    assert product.sku == "LAPTOP-001"
    assert product.name == "Business Laptop"
    assert product.barcode == "123456789"
    assert product.category == "Electronics"
    assert product.base_price == Decimal("50000000")


def test_serial_tracking_is_enabled():
    product = create_serialized_product()

    assert product.serial_tracking is True


def test_serialized_product_price_get():
    product = create_serialized_product()

    assert product.price_get() == Decimal("50000000")


def test_serialized_product_get_price():
    product = create_serialized_product()

    assert product.get_price() == Decimal("50000000")


def test_serialized_product_price_methods_match():
    product = create_serialized_product()

    assert product.price_get() == product.get_price()


def test_serialized_product_accepts_zero_price():
    product = SerializedProduct(
        sku="LAPTOP-001",
        name="Free Laptop",
        barcode="123456789",
        category="Electronics",
        base_price=Decimal("0"),
    )

    assert product.price_get() == Decimal("0")


def test_serialized_product_rejects_negative_price():
    with pytest.raises(ValueError):
        SerializedProduct(
            sku="LAPTOP-001",
            name="Business Laptop",
            barcode="123456789",
            category="Electronics",
            base_price=Decimal("-1"),
        )


def test_serialized_product_rejects_non_decimal_price():
    with pytest.raises(ValueError):
        SerializedProduct(
            sku="LAPTOP-001",
            name="Business Laptop",
            barcode="123456789",
            category="Electronics",
            base_price=50000000,
        )


def test_serialized_product_requires_valid_sku():
    with pytest.raises(ValueError):
        SerializedProduct(
            sku="",
            name="Business Laptop",
            barcode="123456789",
            category="Electronics",
            base_price=Decimal("50000000"),
        )


def test_serialized_product_requires_valid_name():
    with pytest.raises(ValueError):
        SerializedProduct(
            sku="LAPTOP-001",
            name="",
            barcode="123456789",
            category="Electronics",
            base_price=Decimal("50000000"),
        )