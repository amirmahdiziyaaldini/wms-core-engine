import pytest
from decimal import Decimal

from app.domain.models.base_product import BaseProduct
from app.domain.models.bundle_component import BundleComponent
from app.domain.models.bundle_product import BundleProduct


def create_book():
    return BaseProduct(
        sku="BOOK-001",
        name="Python Book",
        barcode="111111111",
        category="Books",
        base_price=Decimal("500000"),
    )


def create_flash_drive():
    return BaseProduct(
        sku="FLASH-001",
        name="Flash Drive",
        barcode="222222222",
        category="Accessories",
        base_price=Decimal("200000"),
    )


def create_bundle(components):
    return BundleProduct(
        sku="BUNDLE-001",
        name="Educational Bundle",
        barcode="999999999",
        category="Education",
        base_price=Decimal("900000"),
        components=components,
    )


def test_create_bundle_product():
    book = create_book()
    flash_drive = create_flash_drive()

    bundle = create_bundle(
        [
            BundleComponent(book, 1),
            BundleComponent(flash_drive, 2),
        ]
    )

    assert bundle.sku == "BUNDLE-001"
    assert bundle.name == "Educational Bundle"
    assert bundle.base_price == Decimal("900000")
    assert len(bundle.components) == 2


def test_bundle_must_have_at_least_one_component():
    with pytest.raises(ValueError):
        create_bundle([])


def test_components_must_be_bundle_components():
    book = create_book()

    with pytest.raises(ValueError):
        create_bundle([book])


def test_bundle_price_is_independent_from_component_prices():
    book = create_book()
    flash_drive = create_flash_drive()

    bundle = create_bundle(
        [
            BundleComponent(book, 1),
            BundleComponent(flash_drive, 2),
        ]
    )

    assert bundle.get_price() == Decimal("900000")


def test_get_sellable_quantity():
    book = create_book()
    flash_drive = create_flash_drive()

    bundle = create_bundle(
        [
            BundleComponent(book, 1),
            BundleComponent(flash_drive, 2),
        ]
    )

    available_stock = {
        "BOOK-001": 10,
        "FLASH-001": 7,
    }

    assert bundle.get_sellable_quantity(available_stock) == 3


def test_get_sellable_quantity_when_component_is_missing():
    book = create_book()
    flash_drive = create_flash_drive()

    bundle = create_bundle(
        [
            BundleComponent(book, 1),
            BundleComponent(flash_drive, 2),
        ]
    )

    available_stock = {
        "BOOK-001": 10,
    }

    assert bundle.get_sellable_quantity(available_stock) == 0


def test_nested_bundle():
    book = create_book()
    flash_drive = create_flash_drive()

    small_bundle = create_bundle(
        [
            BundleComponent(book, 1),
            BundleComponent(flash_drive, 2),
        ]
    )

    large_bundle = BundleProduct(
        sku="BUNDLE-002",
        name="Large Educational Bundle",
        barcode="888888888",
        category="Education",
        base_price=Decimal("1500000"),
        components=[
            BundleComponent(small_bundle, 2),
        ],
    )

    available_stock = {
        "BOOK-001": 10,
        "FLASH-001": 7,
    }

    assert small_bundle.get_sellable_quantity(available_stock) == 3
    assert large_bundle.get_sellable_quantity(available_stock) == 1


def test_bundle_cannot_contain_itself():
    book = create_book()

    bundle = create_bundle(
        [
            BundleComponent(book, 1),
        ]
    )

    with pytest.raises(ValueError):
        bundle.add_component(bundle, 1)


def test_circular_bundle_reference_is_rejected():
    book = create_book()

    bundle_a = create_bundle(
        [
            BundleComponent(book, 1),
        ]
    )

    bundle_b = create_bundle(
        [
            BundleComponent(bundle_a, 1),
        ]
    )

    with pytest.raises(ValueError):
        bundle_a.add_component(bundle_b, 1)


def test_bundle_to_dict():
    book = create_book()
    flash_drive = create_flash_drive()

    bundle = create_bundle(
        [
            BundleComponent(book, 1),
            BundleComponent(flash_drive, 2),
        ]
    )

    data = bundle.to_dict()

    assert data == {
        "sku": "BUNDLE-001",
        "name": "Educational Bundle",
        "barcode": "999999999",
        "category": "Education",
        "base_price": "900000",
        "components": [
            {
                "product_sku": "BOOK-001",
                "required_quantity": 1,
            },
            {
                "product_sku": "FLASH-001",
                "required_quantity": 2,
            },
        ],
    }