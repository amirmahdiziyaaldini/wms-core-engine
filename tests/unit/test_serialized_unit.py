from decimal import Decimal

import pytest

from app.domain.models.base_product import BaseProduct
from app.domain.models.serialized_product import SerializedProduct
from app.domain.models.serialized_unit import SerializedUnit


def create_serialized_product():
    return SerializedProduct(
        sku="LAPTOP-001",
        name="Business Laptop",
        barcode="123456789",
        category="Electronics",
        base_price=Decimal("50000000"),
    )


def test_create_serialized_unit():
    product = create_serialized_product()

    unit = SerializedUnit(
        serial_number="SN-1001",
        product=product,
    )

    assert unit.serial_number == "SN-1001"
    assert unit.product is product


def test_serial_number_must_be_string():
    product = create_serialized_product()

    with pytest.raises(
        ValueError,
        match="Serial number must be a string",
    ):
        SerializedUnit(
            serial_number=1001,
            product=product,
        )


def test_serial_number_cannot_be_empty():
    product = create_serialized_product()

    with pytest.raises(
        ValueError,
        match="Serial number cannot be empty",
    ):
        SerializedUnit(
            serial_number="",
            product=product,
        )


def test_serial_number_cannot_contain_only_whitespace():
    product = create_serialized_product()

    with pytest.raises(
        ValueError,
        match="Serial number cannot be empty",
    ):
        SerializedUnit(
            serial_number="   ",
            product=product,
        )


def test_product_must_be_serialized_product():
    product = BaseProduct(
        sku="BOOK-001",
        name="Python Book",
        barcode="987654321",
        category="Books",
        base_price=Decimal("500000"),
    )

    with pytest.raises(
        ValueError,
        match="Product must be a SerializedProduct",
    ):
        SerializedUnit(
            serial_number="SN-1001",
            product=product,
        )


def test_serialized_unit_keeps_product_reference():
    product = create_serialized_product()

    unit = SerializedUnit(
        serial_number="SN-1001",
        product=product,
    )

    assert unit.product is product


def test_serialized_unit_keeps_serial_number():
    product = create_serialized_product()

    unit = SerializedUnit(
        serial_number="SN-1001",
        product=product,
    )

    assert unit.serial_number == "SN-1001"