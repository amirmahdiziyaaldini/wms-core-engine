import pytest
from decimal import Decimal

from app.domain.enums.warehouse_type import WarehouseType
from app.domain.models.base_product import BaseProduct
from app.domain.models.batch import Batch
from app.domain.models.inventory import Inventory
from app.domain.models.warehouse import Warehouse


def create_warehouse():
    return Warehouse(
        warehouse_id="WH-001",
        name="Central Warehouse",
        location="Tehran",
        warehouse_type=WarehouseType.CENTRAL,
    )


def create_product():
    return BaseProduct(
        sku="BOOK-001",
        name="Python Book",
        barcode="123456789",
        category="Books",
        base_price=Decimal("500000"),
    )


def test_create_inventory():
    warehouse = create_warehouse()

    inventory = Inventory(warehouse)

    assert inventory.warehouse == warehouse
    assert inventory.batches == []


def test_inventory_requires_warehouse():
    with pytest.raises(
        ValueError,
        match="Warehouse must be a Warehouse",
    ):
        Inventory("WH-001")


def test_add_batch():
    warehouse = create_warehouse()
    product = create_product()

    batch = Batch(
        batch_id="BATCH-001",
        product=product,
        quantity=10,
    )

    inventory = Inventory(warehouse)

    inventory.add_batch(batch)

    assert inventory.batches == [batch]


def test_add_batch_requires_batch():
    warehouse = create_warehouse()
    inventory = Inventory(warehouse)

    with pytest.raises(
        ValueError,
        match="Batch must be a Batch",
    ):
        inventory.add_batch("BATCH-001")