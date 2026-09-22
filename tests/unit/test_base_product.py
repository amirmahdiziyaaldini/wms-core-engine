import pytest
from decimal import Decimal

from app.domain.models.base_product import BaseProduct


def test_create_base_product():
    product = BaseProduct(
        sku="BOOK-001",
        name="Python Fundamentals",
        barcode="123456789",
        category="Books",
        base_price=Decimal("500000"),
    )

    assert product.sku == "BOOK-001"
    assert product.name == "Python Fundamentals"
    assert product.barcode == "123456789"
    assert product.category == "Books"
    assert product.base_price == Decimal("500000")


def test_empty_sku():
    with pytest.raises(ValueError):
        BaseProduct(
            sku="",
            name="Python Fundamentals",
            barcode="123456789",
            category="Books",
            base_price=Decimal("500000"),
        )


def test_empty_name():
    with pytest.raises(ValueError):
        BaseProduct(
            sku="BOOK-001",
            name="",
            barcode="123456789",
            category="Books",
            base_price=Decimal("500000"),
        )


def test_empty_barcode():
    with pytest.raises(ValueError):
        BaseProduct(
            sku="BOOK-001",
            name="Python Fundamentals",
            barcode="",
            category="Books",
            base_price=Decimal("500000"),
        )


def test_empty_category():
    with pytest.raises(ValueError):
        BaseProduct(
            sku="BOOK-001",
            name="Python Fundamentals",
            barcode="123456789",
            category="",
            base_price=Decimal("500000"),
        )


def test_base_price_must_be_decimal():
    with pytest.raises(ValueError):
        BaseProduct(
            sku="BOOK-001",
            name="Python Fundamentals",
            barcode="123456789",
            category="Books",
            base_price=500000,
        )


def test_negative_base_price():
    with pytest.raises(ValueError):
        BaseProduct(
            sku="BOOK-001",
            name="Python Fundamentals",
            barcode="123456789",
            category="Books",
            base_price=Decimal("-100"),
        )


def test_zero_base_price():
    product = BaseProduct(
        sku="BOOK-001",
        name="Python Fundamentals",
        barcode="123456789",
        category="Books",
        base_price=Decimal("0"),
    )

    assert product.base_price == Decimal("0")


def test_get_price():
    product = BaseProduct(
        sku="BOOK-001",
        name="Python Fundamentals",
        barcode="123456789",
        category="Books",
        base_price=Decimal("500000"),
    )

    assert product.get_price() == Decimal("500000")


def test_to_dict():
    product = BaseProduct(
        sku="BOOK-001",
        name="Python Fundamentals",
        barcode="123456789",
        category="Books",
        base_price=Decimal("500000"),
    )

    result = product.to_dict()

    assert result == {
        "sku": "BOOK-001",
        "name": "Python Fundamentals",
        "barcode": "123456789",
        "category": "Books",
        "base_price": "500000",
    }