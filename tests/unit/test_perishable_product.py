from decimal import Decimal

from app.domain.models.perishable_product import PerishableProduct


def test_create_perishable_product():
    product = PerishableProduct(
        sku="MILK-001",
        name="Fresh Milk",
        barcode="123456789",
        category="Food",
        base_price=Decimal("50000"),
    )

    assert product.sku == "MILK-001"
    assert product.name == "Fresh Milk"
    assert product.barcode == "123456789"
    assert product.category == "Food"
    assert product.base_price == Decimal("50000")


def test_expiry_tracking_is_enabled():
    product = PerishableProduct(
        sku="MILK-001",
        name="Fresh Milk",
        barcode="123456789",
        category="Food",
        base_price=Decimal("50000"),
    )

    assert product.expiry_tracking is True


def test_perishable_product_get_price():
    product = PerishableProduct(
        sku="MILK-001",
        name="Fresh Milk",
        barcode="123456789",
        category="Food",
        base_price=Decimal("50000"),
    )

    assert product.get_price() == Decimal("50000")