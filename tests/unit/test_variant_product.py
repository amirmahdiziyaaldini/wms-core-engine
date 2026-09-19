import pytest
from decimal import Decimal

from app.domain.models.base_product import BaseProduct
from app.domain.models.variant_product import VariantProduct


def create_parent_product():
    return BaseProduct(
        sku="TSHIRT-001",
        name="T-Shirt",
        barcode="123456789",
        category="Clothing",
        base_price=Decimal("1000000"),
    )


def test_create_variant_product():
    parent_product = create_parent_product()

    variant = VariantProduct(
        sku="TSHIRT-RED-XL",
        name="T-Shirt Red XL",
        barcode="987654321",
        category="Clothing",
        attributes={
            "color": "Red",
            "size": "XL",
        },
        price_modifier=Decimal("150000"),
        parent_product=parent_product,
    )

    assert variant.sku == "TSHIRT-RED-XL"
    assert variant.name == "T-Shirt Red XL"
    assert variant.barcode == "987654321"
    assert variant.category == "Clothing"
    assert variant.base_price == Decimal("1000000")

    assert variant.attributes == {
        "color": "Red",
        "size": "XL",
    }

    assert variant.price_modifier == Decimal("150000")
    assert variant.parent_product == parent_product


def test_variant_attributes_must_be_dict():
    parent_product = create_parent_product()

    with pytest.raises(ValueError):
        VariantProduct(
            sku="TSHIRT-RED-XL",
            name="T-Shirt Red XL",
            barcode="987654321",
            category="Clothing",
            attributes="Red",
            price_modifier=Decimal("150000"),
            parent_product=parent_product,
        )


def test_variant_price_modifier_must_be_decimal():
    parent_product = create_parent_product()

    with pytest.raises(ValueError):
        VariantProduct(
            sku="TSHIRT-RED-XL",
            name="T-Shirt Red XL",
            barcode="987654321",
            category="Clothing",
            attributes={
                "color": "Red",
                "size": "XL",
            },
            price_modifier=150000,
            parent_product=parent_product,
        )


def test_variant_parent_product_must_be_base_product():
    with pytest.raises(ValueError):
        VariantProduct(
            sku="TSHIRT-RED-XL",
            name="T-Shirt Red XL",
            barcode="987654321",
            category="Clothing",
            attributes={
                "color": "Red",
                "size": "XL",
            },
            price_modifier=Decimal("150000"),
            parent_product="T-Shirt",
        )


def test_variant_get_price_with_positive_modifier():
    parent_product = create_parent_product()

    variant = VariantProduct(
        sku="TSHIRT-RED-XL",
        name="T-Shirt Red XL",
        barcode="987654321",
        category="Clothing",
        attributes={
            "color": "Red",
            "size": "XL",
        },
        price_modifier=Decimal("150000"),
        parent_product=parent_product,
    )

    assert variant.get_price() == Decimal("1150000")


def test_variant_get_price_with_zero_modifier():
    parent_product = create_parent_product()

    variant = VariantProduct(
        sku="TSHIRT-BLACK-L",
        name="T-Shirt Black L",
        barcode="111222333",
        category="Clothing",
        attributes={
            "color": "Black",
            "size": "L",
        },
        price_modifier=Decimal("0"),
        parent_product=parent_product,
    )

    assert variant.get_price() == Decimal("1000000")


def test_variant_get_price_with_negative_modifier():
    parent_product = create_parent_product()

    variant = VariantProduct(
        sku="TSHIRT-SALE-L",
        name="T-Shirt Sale L",
        barcode="444555666",
        category="Clothing",
        attributes={
            "color": "Blue",
            "size": "L",
        },
        price_modifier=Decimal("-100000"),
        parent_product=parent_product,
    )

    assert variant.get_price() == Decimal("900000")


def test_variant_final_price_cannot_be_negative():
    parent_product = create_parent_product()

    variant = VariantProduct(
        sku="TSHIRT-INVALID",
        name="Invalid T-Shirt",
        barcode="777888999",
        category="Clothing",
        attributes={
            "color": "Red",
            "size": "XL",
        },
        price_modifier=Decimal("-1500000"),
        parent_product=parent_product,
    )

    with pytest.raises(ValueError):
        variant.get_price()


def test_variant_to_dict():
    parent_product = create_parent_product()

    variant = VariantProduct(
        sku="TSHIRT-RED-XL",
        name="T-Shirt Red XL",
        barcode="987654321",
        category="Clothing",
        attributes={
            "color": "Red",
            "size": "XL",
        },
        price_modifier=Decimal("150000"),
        parent_product=parent_product,
    )

    result = variant.to_dict()

    assert result == {
        "sku": "TSHIRT-RED-XL",
        "name": "T-Shirt Red XL",
        "barcode": "987654321",
        "category": "Clothing",
        "base_price": "1000000",
        "attributes": {
            "color": "Red",
            "size": "XL",
        },
        "price_modifier": "150000",
        "parent_product_sku": "TSHIRT-001",
    }