from datetime import datetime

import pytest

from app.domain.enums.inventory_transaction_type import (
    InventoryTransactionType,
)
from app.domain.enums.warehouse_type import WarehouseType
from app.domain.models.inventory_ledger import (
    InventoryLedger,
)
from app.domain.models.warehouse import Warehouse
from app.services.inventory_service import InventoryService


def create_warehouse():
    return Warehouse(
        warehouse_id="WH-001",
        name="Central Warehouse",
        location="Tehran",
        warehouse_type=WarehouseType.CENTRAL,
    )


def create_service():
    ledger = InventoryLedger()

    return InventoryService(ledger)


def test_create_inventory_service():
    ledger = InventoryLedger()

    service = InventoryService(ledger)

    assert service.ledger == ledger


def test_inventory_service_requires_ledger():
    with pytest.raises(
        ValueError,
        match="Ledger must be an InventoryLedger",
    ):
        InventoryService("invalid ledger")


def test_record_transaction():
    ledger = InventoryLedger()
    service = InventoryService(ledger)

    transaction = service.record_transaction(
        timestamp=datetime(2026, 9, 23, 10, 30),
        warehouse=create_warehouse(),
        sku="LAPTOP-01",
        quantity=10,
        transaction_type=InventoryTransactionType.RECEIVE,
        reference_id="REC-001",
    )

    assert transaction.sku == "LAPTOP-01"
    assert transaction.quantity == 10
    assert (
        transaction.transaction_type
        == InventoryTransactionType.RECEIVE
    )


def test_record_transaction_adds_to_ledger():
    ledger = InventoryLedger()
    service = InventoryService(ledger)

    transaction = service.record_transaction(
        timestamp=datetime(2026, 9, 23, 10, 30),
        warehouse=create_warehouse(),
        sku="LAPTOP-01",
        quantity=10,
        transaction_type=InventoryTransactionType.RECEIVE,
        reference_id="REC-001",
    )

    assert ledger.transactions == [transaction]