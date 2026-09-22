from datetime import date
from decimal import Decimal

import pytest

from app.domain.models.base_product import BaseProduct
from app.domain.models.batch import Batch
from app.domain.models.perishable_product import PerishableProduct


def test_create_batch_for_regular_product():
    product = BaseProduct(
        sku="BOOK-001",
        name="Python Book",
        barcode="111111111",
        category="Books",
        base_price=Decimal("500000"),
    )

    batch = Batch(
        batch_id="BATCH-001",
        product=product,
        quantity=10,
    )

    assert batch.batch_id == "BATCH-001"
    assert batch.product is product
    assert batch.quantity == 10
    assert batch.expiry_date is None


def test_perishable_product_requires_expiry_date():
    product = PerishableProduct(
        sku="MILK-001",
        name="Fresh Milk",
        barcode="123456789",
        category="Food",
        base_price=Decimal("50000"),
    )

    with pytest.raises(ValueError):
        Batch(
            batch_id="BATCH-001",
            product=product,
            quantity=10,
        )


def test_create_batch_for_perishable_product():
    product = PerishableProduct(
        sku="MILK-001",
        name="Fresh Milk",
        barcode="123456789",
        category="Food",
        base_price=Decimal("50000"),
    )

    expiry_date = date(2026, 10, 1)

    batch = Batch(
        batch_id="BATCH-001",
        product=product,
        quantity=10,
        expiry_date=expiry_date,
    )

    assert batch.expiry_date == expiry_date


def test_expired_batch():
    product = PerishableProduct(
        sku="MILK-001",
        name="Fresh Milk",
        barcode="123456789",
        category="Food",
        base_price=Decimal("50000"),
    )

    batch = Batch(
        batch_id="BATCH-001",
        product=product,
        quantity=10,
        expiry_date=date(2026, 8, 1),
    )

    assert batch.is_expired(
        date(2026, 9, 1)
    ) is True


def test_non_expired_batch():
    product = PerishableProduct(
        sku="MILK-001",
        name="Fresh Milk",
        barcode="123456789",
        category="Food",
        base_price=Decimal("50000"),
    )

    batch = Batch(
        batch_id="BATCH-001",
        product=product,
        quantity=10,
        expiry_date=date(2026, 10, 1),
    )

    assert batch.is_expired(
        date(2026, 9, 1)
    ) is False


def test_regular_product_batch_is_not_expired():
    product = BaseProduct(
        sku="BOOK-001",
        name="Python Book",
        barcode="111111111",
        category="Books",
        base_price=Decimal("500000"),
    )

    batch = Batch(
        batch_id="BATCH-001",
        product=product,
        quantity=10,
    )

    assert batch.is_expired(
        date(2026, 9, 1)
    ) is False

def test_batch_id_must_be_string():
    product = BaseProduct(
        sku="BOOK-001",
        name="Python Book",
        barcode="111111111",
        category="Books",
        base_price=Decimal("500000"),
    )

    with pytest.raises(ValueError):
        Batch(
            batch_id=123,
            product=product,
            quantity=10,
        )


def test_batch_id_cannot_be_empty():
    product = BaseProduct(
        sku="BOOK-001",
        name="Python Book",
        barcode="111111111",
        category="Books",
        base_price=Decimal("500000"),
    )

    with pytest.raises(ValueError):
        Batch(
            batch_id="",
            product=product,
            quantity=10,
        )


def test_product_must_be_base_product():
    with pytest.raises(ValueError):
        Batch(
            batch_id="BATCH-001",
            product="BOOK-001",
            quantity=10,
        )


def test_quantity_must_be_integer():
    product = BaseProduct(
        sku="BOOK-001",
        name="Python Book",
        barcode="111111111",
        category="Books",
        base_price=Decimal("500000"),
    )

    with pytest.raises(ValueError):
        Batch(
            batch_id="BATCH-001",
            product=product,
            quantity="10",
        )


def test_quantity_must_be_greater_than_zero():
    product = BaseProduct(
        sku="BOOK-001",
        name="Python Book",
        barcode="111111111",
        category="Books",
        base_price=Decimal("500000"),
    )

    with pytest.raises(ValueError):
        Batch(
            batch_id="BATCH-001",
            product=product,
            quantity=0,
        )


def test_quantity_cannot_be_negative():
    product = BaseProduct(
        sku="BOOK-001",
        name="Python Book",
        barcode="111111111",
        category="Books",
        base_price=Decimal("500000"),
    )

    with pytest.raises(ValueError):
        Batch(
            batch_id="BATCH-001",
            product=product,
            quantity=-5,
        )


def test_expiry_date_must_be_date():
    product = PerishableProduct(
        sku="MILK-001",
        name="Fresh Milk",
        barcode="123456789",
        category="Food",
        base_price=Decimal("50000"),
    )

    with pytest.raises(ValueError):
        Batch(
            batch_id="BATCH-001",
            product=product,
            quantity=10,
            expiry_date="2026-10-01",
        )