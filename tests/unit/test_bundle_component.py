import pytest
from decimal import Decimal

from app.domain.models.base_product import BaseProduct
from app.domain.models.bundle_component import BundleComponent


def create_product():
    return BaseProduct(
        sku="BOOK-001",
        name="Python Book",
        barcode="123456789",
        category="Books",
        base_price=Decimal("500000"),
    )


def test_create_bundle_component():
    product = create_product()

    component = BundleComponent(
        product=product,
        required_quantity=2,
    )

    assert component.product == product
    assert component.required_quantity == 2


def test_product_must_be_base_product():
    with pytest.raises(ValueError):
        BundleComponent(
            product="Book",
            required_quantity=2,
        )


def test_required_quantity_must_be_integer():
    product = create_product()

    with pytest.raises(ValueError):
        BundleComponent(
            product=product,
            required_quantity=2.5,
        )


def test_required_quantity_must_be_positive():
    product = create_product()

    with pytest.raises(ValueError):
        BundleComponent(
            product=product,
            required_quantity=0,
        )

    with pytest.raises(ValueError):
        BundleComponent(
            product=product,
            required_quantity=-1,
        )