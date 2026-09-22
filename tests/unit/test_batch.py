from datetime import date
from decimal import Decimal

import pytest

from app.domain.models.base_product import BaseProduct
from app.domain.models.batch import Batch
from app.domain.models.serialized_product import SerializedProduct


def create_base_product():
    return BaseProduct(
        sku="BOOK-001",
        name="Python Book",
        barcode="987654321",
        category="Books",
        base_price=Decimal("500000"),
    )


def create_serialized_product():
    return SerializedProduct(
        sku="LAPTOP-001",
        name="Business Laptop",
        barcode="123456789",
        category="Electronics",
        base_price=Decimal("50000000"),
    )


def test_create_batch():
    product = create_base_product()

    batch = Batch(
        batch_id="BATCH-001",
        product=product,
        quantity=10,
    )

    assert batch.batch_id == "BATCH-001"
    assert batch.product is product
    assert batch.quantity == 10
    assert batch.expiry_date is None
    assert batch.serial_numbers is None


def test_create_perishable_batch_requires_expiry_date():
    product = BaseProduct(
        sku="MILK-001",
        name="Fresh Milk",
        barcode="111111111",
        category="Food",
        base_price=Decimal("50000"),
    )

    product.expiry_tracking = True

    with pytest.raises(
        ValueError,
        match="Expiry date is required for perishable products",
    ):
        Batch(
            batch_id="BATCH-001",
            product=product,
            quantity=10,
        )


def test_create_perishable_batch_with_expiry_date():
    product = BaseProduct(
        sku="MILK-001",
        name="Fresh Milk",
        barcode="111111111",
        category="Food",
        base_price=Decimal("50000"),
    )

    product.expiry_tracking = True

    expiry_date = date(2026, 12, 31)

    batch = Batch(
        batch_id="BATCH-001",
        product=product,
        quantity=10,
        expiry_date=expiry_date,
    )

    assert batch.expiry_date == expiry_date


def test_expired_batch():
    product = create_base_product()

    batch = Batch(
        batch_id="BATCH-001",
        product=product,
        quantity=10,
        expiry_date=date(2026, 1, 1),
    )

    assert batch.is_expired(
        reference_date=date(2026, 2, 1)
    ) is True


def test_non_expired_batch():
    product = create_base_product()

    batch = Batch(
        batch_id="BATCH-001",
        product=product,
        quantity=10,
        expiry_date=date(2026, 12, 31),
    )

    assert batch.is_expired(
        reference_date=date(2026, 6, 1)
    ) is False


def test_regular_product_batch_is_not_expired():
    product = create_base_product()

    batch = Batch(
        batch_id="BATCH-001",
        product=product,
        quantity=10,
    )

    assert batch.is_expired(
        reference_date=date(2026, 6, 1)
    ) is False


def test_batch_id_must_be_string():
    product = create_base_product()

    with pytest.raises(
        ValueError,
        match="Batch ID must be a string",
    ):
        Batch(
            batch_id=1001,
            product=product,
            quantity=10,
        )


def test_batch_id_cannot_be_empty():
    product = create_base_product()

    with pytest.raises(
        ValueError,
        match="Batch ID cannot be empty",
    ):
        Batch(
            batch_id="",
            product=product,
            quantity=10,
        )


def test_product_must_be_base_product():
    with pytest.raises(
        ValueError,
        match="Product must be a BaseProduct",
    ):
        Batch(
            batch_id="BATCH-001",
            product="BOOK-001",
            quantity=10,
        )


def test_quantity_must_be_integer():
    product = create_base_product()

    with pytest.raises(
        ValueError,
        match="Quantity must be an integer",
    ):
        Batch(
            batch_id="BATCH-001",
            product=product,
            quantity="10",
        )


def test_quantity_must_be_greater_than_zero():
    product = create_base_product()

    with pytest.raises(
        ValueError,
        match="Quantity must be greater than zero",
    ):
        Batch(
            batch_id="BATCH-001",
            product=product,
            quantity=0,
        )


def test_quantity_cannot_be_negative():
    product = create_base_product()

    with pytest.raises(
        ValueError,
        match="Quantity must be greater than zero",
    ):
        Batch(
            batch_id="BATCH-001",
            product=product,
            quantity=-5,
        )


def test_expiry_date_must_be_date():
    product = create_base_product()

    with pytest.raises(
        ValueError,
        match="Expiry date must be a date",
    ):
        Batch(
            batch_id="BATCH-001",
            product=product,
            quantity=10,
            expiry_date="2026-12-31",
        )


def test_serialized_product_batch_requires_serial_numbers():
    product = create_serialized_product()

    with pytest.raises(
        ValueError,
        match="Serial numbers are required for serialized products",
    ):
        Batch(
            batch_id="BATCH-001",
            product=product,
            quantity=2,
        )


def test_serial_numbers_count_must_match_quantity():
    product = create_serialized_product()

    with pytest.raises(
        ValueError,
        match="Number of serial numbers must match quantity",
    ):
        Batch(
            batch_id="BATCH-001",
            product=product,
            quantity=3,
            serial_numbers=[
                "SN-1001",
                "SN-1002",
            ],
        )


def test_serialized_batch_can_be_created_with_correct_serial_numbers():
    product = create_serialized_product()

    batch = Batch(
        batch_id="BATCH-001",
        product=product,
        quantity=3,
        serial_numbers=[
            "SN-1001",
            "SN-1002",
            "SN-1003",
        ],
    )

    assert batch.serial_numbers == [
        "SN-1001",
        "SN-1002",
        "SN-1003",
    ]


def test_serial_numbers_must_be_a_list():
    product = create_serialized_product()

    with pytest.raises(
        ValueError,
        match="Serial numbers must be a list",
    ):
        Batch(
            batch_id="BATCH-001",
            product=product,
            quantity=1,
            serial_numbers="SN-1001",
        )


def test_serial_number_must_be_a_string():
    product = create_serialized_product()

    with pytest.raises(
        ValueError,
        match="Serial number must be a string",
    ):
        Batch(
            batch_id="BATCH-001",
            product=product,
            quantity=1,
            serial_numbers=[1001],
        )


def test_serial_number_cannot_be_empty():
    product = create_serialized_product()

    with pytest.raises(
        ValueError,
        match="Serial number cannot be empty",
    ):
        Batch(
            batch_id="BATCH-001",
            product=product,
            quantity=1,
            serial_numbers=[""],
        )


def test_serial_number_cannot_contain_only_whitespace():
    product = create_serialized_product()

    with pytest.raises(
        ValueError,
        match="Serial number cannot be empty",
    ):
        Batch(
            batch_id="BATCH-001",
            product=product,
            quantity=1,
            serial_numbers=["   "],
        )


def test_serial_numbers_must_be_unique():
    product = create_serialized_product()

    with pytest.raises(
        ValueError,
        match="Serial numbers must be unique",
    ):
        Batch(
            batch_id="BATCH-001",
            product=product,
            quantity=3,
            serial_numbers=[
                "SN-1001",
                "SN-1002",
                "SN-1001",
            ],
        )


def test_serialized_batch_accepts_multiple_unique_serial_numbers():
    product = create_serialized_product()

    batch = Batch(
        batch_id="BATCH-001",
        product=product,
        quantity=4,
        serial_numbers=[
            "SN-1001",
            "SN-1002",
            "SN-1003",
            "SN-1004",
        ],
    )

    assert len(batch.serial_numbers) == 4
    assert len(set(batch.serial_numbers)) == 4


def test_non_serialized_product_can_have_no_serial_numbers():
    product = create_base_product()

    batch = Batch(
        batch_id="BATCH-001",
        product=product,
        quantity=5,
    )

    assert batch.serial_numbers is None