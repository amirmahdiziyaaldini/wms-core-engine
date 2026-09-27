import json
from decimal import Decimal

import pytest

from app.domain.models.base_product import BaseProduct
from app.serialization.deserializer import (
    DeserializationContext,
    DeserializationError,
    deserialize_product,
    from_json,
    load_products,
)


def test_deserialize_base_product():
    data = {
        "type": "BaseProduct",
        "product_type": "BaseProduct",
        "sku": "BOOK-001",
        "name": "Python Fundamentals",
        "barcode": "123456789",
        "category": "Books",
        "base_price": "500000",
    }

    context = DeserializationContext()

    product = deserialize_product(data, context)

    assert isinstance(product, BaseProduct)
    assert product.sku == "BOOK-001"
    assert product.name == "Python Fundamentals"
    assert product.barcode == "123456789"
    assert product.category == "Books"
    assert product.base_price == Decimal("500000")


def test_deserialize_product_from_json():
    value = json.dumps(
        {
            "type": "BaseProduct",
            "product_type": "BaseProduct",
            "sku": "BOOK-002",
            "name": "Python OOP",
            "barcode": "987654321",
            "category": "Books",
            "base_price": "250000",
        }
    )

    product = from_json(value)

    assert product.sku == "BOOK-002"
    assert product.base_price == Decimal("250000")


def test_context_stores_product_by_sku():
    context = DeserializationContext()

    data = {
        "type": "BaseProduct",
        "product_type": "BaseProduct",
        "sku": "BOOK-003",
        "name": "Python",
        "barcode": "111111111",
        "category": "Books",
        "base_price": "100000",
    }

    product = deserialize_product(data, context)

    assert context.get_product("BOOK-003") is product


def test_missing_product_reference_raises_error():
    context = DeserializationContext()

    data = {
        "type": "VariantProduct",
        "product_type": "VariantProduct",
        "sku": "VAR-001",
        "name": "Variant",
        "barcode": "222222222",
        "category": "Books",
        "base_price": "100000",
        "parent_product_sku": "BOOK-999",
        "price_modifier": "10000",
        "attributes": {},
    }

    with pytest.raises(DeserializationError):
        deserialize_product(data, context)


def test_unknown_product_type_raises_error():
    context = DeserializationContext()

    data = {
        "type": "UnknownProduct",
        "product_type": "UnknownProduct",
        "sku": "UNKNOWN-001",
        "name": "Unknown",
        "barcode": "333333333",
        "category": "Other",
        "base_price": "100000",
    }

    with pytest.raises(DeserializationError):
        deserialize_product(data, context)


def test_load_products():
    data = [
        {
            "type": "BaseProduct",
            "product_type": "BaseProduct",
            "sku": "BOOK-001",
            "name": "Book",
            "barcode": "444444444",
            "category": "Books",
            "base_price": "100000",
        },
        {
            "type": "BaseProduct",
            "product_type": "BaseProduct",
            "sku": "BOOK-002",
            "name": "Second Book",
            "barcode": "555555555",
            "category": "Books",
            "base_price": "200000",
        },
    ]

    products = load_products(data)

    assert len(products) == 2
    assert products[0].sku == "BOOK-001"
    assert products[1].sku == "BOOK-002"


def test_deserialize_variant_product_uses_parent_product_reference():
    context = DeserializationContext()

    parent = deserialize_product(
        {
            "type": "BaseProduct",
            "sku": "BOOK-001",
            "name": "Python Book",
            "barcode": "123456",
            "category": "Books",
            "base_price": "500000",
        },
        context,
    )

    variant = deserialize_product(
        {
            "type": "VariantProduct",
            "sku": "BOOK-001-BLUE",
            "name": "Python Book Blue",
            "barcode": "123457",
            "category": "Books",
            "attributes": {
                "color": "blue",
            },
            "price_modifier": "50000",
            "parent_product_sku": "BOOK-001",
        },
        context,
    )

    assert variant.parent_product is parent
    assert variant.parent_product.sku == "BOOK-001"


def test_deserialize_bundle_product_uses_product_references():
    context = DeserializationContext()

    product = deserialize_product(
        {
            "type": "BaseProduct",
            "sku": "BOOK-001",
            "name": "Python Book",
            "barcode": "123456",
            "category": "Books",
            "base_price": "500000",
        },
        context,
    )

    bundle = deserialize_product(
        {
            "type": "BundleProduct",
            "sku": "BUNDLE-001",
            "name": "Python Bundle",
            "barcode": "999999",
            "category": "Bundles",
            "base_price": "800000",
            "components": [
                {
                    "product_sku": "BOOK-001",
                    "required_quantity": 2,
                }
            ],
        },
        context,
    )

    assert bundle.components[0].product is product
    assert bundle.components[0].product.sku == "BOOK-001"
    assert bundle.components[0].required_quantity == 2


def test_load_products_resolves_variant_reference():
    context = DeserializationContext()

    products = load_products(
        [
            {
                "type": "VariantProduct",
                "sku": "BOOK-001-BLUE",
                "name": "Python Book Blue",
                "barcode": "123457",
                "category": "Books",
                "attributes": {
                    "color": "blue",
                },
                "price_modifier": "50000",
                "parent_product_sku": "BOOK-001",
            },
            {
                "type": "BaseProduct",
                "sku": "BOOK-001",
                "name": "Python Book",
                "barcode": "123456",
                "category": "Books",
                "base_price": "500000",
            },
        ],
        context,
    )

    parent = context.get_product("BOOK-001")
    variant = context.get_product("BOOK-001-BLUE")

    assert variant.parent_product is parent
    assert len(products) == 2


def test_load_products_resolves_bundle_references():
    context = DeserializationContext()

    products = load_products(
        [
            {
                "type": "BundleProduct",
                "sku": "BUNDLE-001",
                "name": "Python Bundle",
                "barcode": "999999",
                "category": "Bundles",
                "base_price": "800000",
                "components": [
                    {
                        "product_sku": "BOOK-001",
                        "required_quantity": 2,
                    }
                ],
            },
            {
                "type": "BaseProduct",
                "sku": "BOOK-001",
                "name": "Python Book",
                "barcode": "123456",
                "category": "Books",
                "base_price": "500000",
            },
        ],
        context,
    )

    product = context.get_product("BOOK-001")
    bundle = context.get_product("BUNDLE-001")

    assert bundle.components[0].product is product
    assert len(products) == 2