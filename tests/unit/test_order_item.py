import pytest

from app.domain.models.order_item import OrderItem


def test_create_valid_order_item():
    item = OrderItem(
        item_id="ITEM-001",
        sku="LAPTOP-01",
        quantity=3,
    )

    assert item.item_id == "ITEM-001"
    assert item.sku == "LAPTOP-01"
    assert item.quantity == 3


def test_item_id_must_be_string():
    with pytest.raises(ValueError):
        OrderItem(
            item_id=123,
            sku="LAPTOP-01",
            quantity=3,
        )


def test_item_id_cannot_be_empty():
    with pytest.raises(ValueError):
        OrderItem(
            item_id="",
            sku="LAPTOP-01",
            quantity=3,
        )


def test_item_id_cannot_contain_only_whitespace():
    with pytest.raises(ValueError):
        OrderItem(
            item_id="   ",
            sku="LAPTOP-01",
            quantity=3,
        )


def test_sku_must_be_string():
    with pytest.raises(ValueError):
        OrderItem(
            item_id="ITEM-001",
            sku=123,
            quantity=3,
        )


def test_sku_cannot_be_empty():
    with pytest.raises(ValueError):
        OrderItem(
            item_id="ITEM-001",
            sku="",
            quantity=3,
        )


def test_sku_cannot_contain_only_whitespace():
    with pytest.raises(ValueError):
        OrderItem(
            item_id="ITEM-001",
            sku="   ",
            quantity=3,
        )


def test_quantity_must_be_integer():
    with pytest.raises(ValueError):
        OrderItem(
            item_id="ITEM-001",
            sku="LAPTOP-01",
            quantity=2.5,
        )


def test_quantity_cannot_be_zero():
    with pytest.raises(ValueError):
        OrderItem(
            item_id="ITEM-001",
            sku="LAPTOP-01",
            quantity=0,
        )


def test_quantity_cannot_be_negative():
    with pytest.raises(ValueError):
        OrderItem(
            item_id="ITEM-001",
            sku="LAPTOP-01",
            quantity=-1,
        )


def test_boolean_quantity_is_rejected():
    with pytest.raises(ValueError):
        OrderItem(
            item_id="ITEM-001",
            sku="LAPTOP-01",
            quantity=True,
        )