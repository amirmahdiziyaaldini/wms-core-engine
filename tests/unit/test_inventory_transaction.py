from datetime import datetime
from decimal import Decimal

import pytest

from app.domain.enums.inventory_transaction_type import (
    InventoryTransactionType,
)
from app.domain.enums.warehouse_type import WarehouseType
from app.domain.models.inventory_transaction import (
    InventoryTransaction,
)
from app.domain.models.warehouse import Warehouse


def create_warehouse():
    return Warehouse(
        warehouse_id="WH-001",
        name="Central Warehouse",
        location="Tehran",
        warehouse_type=WarehouseType.CENTRAL,
    )


def create_transaction():
    return InventoryTransaction(
        timestamp=datetime(2026, 9, 23, 10, 30),
        warehouse=create_warehouse(),
        sku="LAPTOP-01",
        quantity=10,
        transaction_type=InventoryTransactionType.RECEIVE,
        reference_id="REC-001",
    )


def test_create_inventory_transaction():
    transaction = create_transaction()

    assert transaction.timestamp == datetime(
        2026,
        9,
        23,
        10,
        30,
    )
    assert transaction.warehouse.warehouse_id == "WH-001"
    assert transaction.sku == "LAPTOP-01"
    assert transaction.quantity == 10
    assert (
        transaction.transaction_type
        == InventoryTransactionType.RECEIVE
    )
    assert transaction.reference_id == "REC-001"


def test_quantity_can_be_negative():
    transaction = InventoryTransaction(
        timestamp=datetime(2026, 9, 23, 10, 30),
        warehouse=create_warehouse(),
        sku="LAPTOP-01",
        quantity=-5,
        transaction_type=InventoryTransactionType.SHIP,
        reference_id="ORD-001",
    )

    assert transaction.quantity == -5


def test_timestamp_must_be_datetime():
    with pytest.raises(
        ValueError,
        match="Timestamp must be a datetime",
    ):
        InventoryTransaction(
            timestamp="2026-09-23",
            warehouse=create_warehouse(),
            sku="LAPTOP-01",
            quantity=10,
            transaction_type=InventoryTransactionType.RECEIVE,
            reference_id="REC-001",
        )


def test_warehouse_must_be_warehouse():
    with pytest.raises(
        ValueError,
        match="Warehouse must be a Warehouse",
    ):
        InventoryTransaction(
            timestamp=datetime(2026, 9, 23, 10, 30),
            warehouse="WH-001",
            sku="LAPTOP-01",
            quantity=10,
            transaction_type=InventoryTransactionType.RECEIVE,
            reference_id="REC-001",
        )


def test_sku_cannot_be_empty():
    with pytest.raises(
        ValueError,
        match="SKU cannot be empty",
    ):
        InventoryTransaction(
            timestamp=datetime(2026, 9, 23, 10, 30),
            warehouse=create_warehouse(),
            sku="",
            quantity=10,
            transaction_type=InventoryTransactionType.RECEIVE,
            reference_id="REC-001",
        )


def test_quantity_cannot_be_zero():
    with pytest.raises(
        ValueError,
        match="Quantity cannot be zero",
    ):
        InventoryTransaction(
            timestamp=datetime(2026, 9, 23, 10, 30),
            warehouse=create_warehouse(),
            sku="LAPTOP-01",
            quantity=0,
            transaction_type=InventoryTransactionType.RECEIVE,
            reference_id="REC-001",
        )


def test_quantity_must_be_integer():
    with pytest.raises(
        ValueError,
        match="Quantity must be an integer",
    ):
        InventoryTransaction(
            timestamp=datetime(2026, 9, 23, 10, 30),
            warehouse=create_warehouse(),
            sku="LAPTOP-01",
            quantity=10.5,
            transaction_type=InventoryTransactionType.RECEIVE,
            reference_id="REC-001",
        )


def test_transaction_type_must_be_valid_enum():
    with pytest.raises(
        ValueError,
        match="Transaction type must be an InventoryTransactionType",
    ):
        InventoryTransaction(
            timestamp=datetime(2026, 9, 23, 10, 30),
            warehouse=create_warehouse(),
            sku="LAPTOP-01",
            quantity=10,
            transaction_type="receive",
            reference_id="REC-001",
        )


def test_reference_id_cannot_be_empty():
    with pytest.raises(
        ValueError,
        match="Reference ID cannot be empty",
    ):
        InventoryTransaction(
            timestamp=datetime(2026, 9, 23, 10, 30),
            warehouse=create_warehouse(),
            sku="LAPTOP-01",
            quantity=10,
            transaction_type=InventoryTransactionType.RECEIVE,
            reference_id="",
        )


def test_required_transaction_types_exist():
    assert InventoryTransactionType.RECEIVE.value == "receive"
    assert InventoryTransactionType.RESERVE.value == "reserve"
    assert (
        InventoryTransactionType.RELEASE_RESERVATION.value
        == "release_reservation"
    )
    assert InventoryTransactionType.SHIP.value == "ship"
    assert InventoryTransactionType.ISSUE.value == "issue"
    assert (
        InventoryTransactionType.TRANSFER_IN.value
        == "transfer_in"
    )
    assert (
        InventoryTransactionType.TRANSFER_OUT.value
        == "transfer_out"
    )
    assert (
        InventoryTransactionType.RETURN_TO_STOCK.value
        == "return_to_stock"
    )
    assert InventoryTransactionType.SCRAP.value == "scrap"