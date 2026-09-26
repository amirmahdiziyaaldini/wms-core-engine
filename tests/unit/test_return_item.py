import pytest

from app.domain.models.return_item import ReturnItem


def test_create_return_item():
    item = ReturnItem(
        sku="LAPTOP-01",
        quantity=2,
    )

    assert item.sku == "LAPTOP-01"
    assert item.quantity == 2
    assert item.serial_numbers is None


def test_create_serialized_return_item():
    item = ReturnItem(
        sku="PHONE-01",
        quantity=2,
        serial_numbers=["SN-001", "SN-002"],
    )

    assert item.serial_numbers == ["SN-001", "SN-002"]


def test_return_item_rejects_empty_sku():
    with pytest.raises(
        ValueError,
        match="SKU cannot be empty",
    ):
        ReturnItem(
            sku="",
            quantity=1,
        )


def test_return_item_rejects_invalid_quantity():
    with pytest.raises(
        ValueError,
        match="Quantity must be positive",
    ):
        ReturnItem(
            sku="LAPTOP-01",
            quantity=0,
        )


def test_return_item_rejects_serial_count_mismatch():
    with pytest.raises(
        ValueError,
        match="Number of serial numbers must match quantity",
    ):
        ReturnItem(
            sku="PHONE-01",
            quantity=2,
            serial_numbers=["SN-001"],
        )


def test_return_item_rejects_duplicate_serial_numbers():
    with pytest.raises(
        ValueError,
        match="Serial numbers must be unique",
    ):
        ReturnItem(
            sku="PHONE-01",
            quantity=2,
            serial_numbers=["SN-001", "SN-001"],
        )