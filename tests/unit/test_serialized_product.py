from decimal import Decimal

from app.domain.models.serialized_product import SerializedProduct


def test_create_serialized_product():
    product = SerializedProduct(
        sku="LAPTOP-001",
        name="Business Laptop",
        barcode="123456789",
        category="Electronics",
        base_price=Decimal("50000000"),
    )

    assert product.sku == "LAPTOP-001"
    assert product.name == "Business Laptop"
    assert product.barcode == "123456789"
    assert product.category == "Electronics"
    assert product.base_price == Decimal("50000000")


def test_serial_tracking_is_enabled():
    product = SerializedProduct(
        sku="LAPTOP-001",
        name="Business Laptop",
        barcode="123456789",
        category="Electronics",
        base_price=Decimal("50000000"),
    )

    assert product.serial_tracking is True


def test_serialized_product_inherits_from_base_product():
    product = SerializedProduct(
        sku="LAPTOP-001",
        name="Business Laptop",
        barcode="123456789",
        category="Electronics",
        base_price=Decimal("50000000"),
    )

    assert product.get_price() == Decimal("50000000")