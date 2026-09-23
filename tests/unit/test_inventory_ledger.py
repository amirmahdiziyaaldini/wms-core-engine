from datetime import datetime

import pytest

from app.domain.enums.inventory_transaction_type import (
    InventoryTransactionType,
)
from app.domain.enums.warehouse_type import WarehouseType
from app.domain.models.inventory_ledger import (
    InventoryLedger,
)
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


def create_transaction(
    reference_id="REC-001",
    quantity=10,
):
    return InventoryTransaction(
        timestamp=datetime(2026, 9, 23, 10, 30),
        warehouse=create_warehouse(),
        sku="LAPTOP-01",
        quantity=quantity,
        transaction_type=InventoryTransactionType.RECEIVE,
        reference_id=reference_id,
    )


def test_create_inventory_ledger():
    ledger = InventoryLedger()

    assert ledger.transactions == []


def test_record_transaction():
    ledger = InventoryLedger()
    transaction = create_transaction()

    ledger.record(transaction)

    assert ledger.transactions == [transaction]


def test_record_multiple_transactions():
    ledger = InventoryLedger()

    first_transaction = create_transaction(
        reference_id="REC-001",
        quantity=10,
    )

    second_transaction = create_transaction(
        reference_id="REC-002",
        quantity=5,
    )

    ledger.record(first_transaction)
    ledger.record(second_transaction)

    assert ledger.transactions == [
        first_transaction,
        second_transaction,
    ]


def test_record_requires_inventory_transaction():
    ledger = InventoryLedger()

    with pytest.raises(
        ValueError,
        match="Transaction must be an InventoryTransaction",
    ):
        ledger.record("invalid transaction")