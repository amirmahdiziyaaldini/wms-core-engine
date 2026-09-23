from decimal import Decimal

import pytest

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


def create_product(sku="LAPTOP-01"):
    return BaseProduct(
        sku=sku,
        name="Laptop",
        barcode="123456789",
        category="Electronics",
        base_price=Decimal("500000"),
    )


def create_batch(quantity=10, sku="LAPTOP-01", batch_id="BATCH-001"):
    return Batch(
        batch_id=batch_id,
        product=create_product(sku),
        quantity=quantity,
    )


def test_add_batch_adds_valid_batch():
    inventory = Inventory(create_warehouse())

    batch = create_batch()

    inventory.add_batch(batch)

    assert batch in inventory.batches


def test_physical_stock_is_calculated_from_batches():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    assert inventory.get_physical_stock("LAPTOP-01") == 10


def test_physical_stock_combines_multiple_batches():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(
            quantity=10,
            batch_id="BATCH-001",
        )
    )

    inventory.add_batch(
        create_batch(
            quantity=5,
            batch_id="BATCH-002",
        )
    )

    assert inventory.get_physical_stock("LAPTOP-01") == 15


def test_reserved_stock_is_zero_without_reservation():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    assert inventory.get_reserved_stock("LAPTOP-01") == 0


def test_available_stock_equals_physical_minus_reserved():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    inventory.reserve(
        reservation_id="ORDER-001",
        sku="LAPTOP-01",
        quantity=3,
    )

    assert inventory.get_physical_stock("LAPTOP-01") == 10
    assert inventory.get_reserved_stock("LAPTOP-01") == 3
    assert inventory.get_available_stock("LAPTOP-01") == 7


def test_reservation_does_not_change_physical_stock():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    inventory.reserve(
        reservation_id="ORDER-001",
        sku="LAPTOP-01",
        quantity=3,
    )

    assert inventory.get_physical_stock("LAPTOP-01") == 10


def test_multiple_reservations_are_combined():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    inventory.reserve(
        reservation_id="ORDER-001",
        sku="LAPTOP-01",
        quantity=3,
    )

    inventory.reserve(
        reservation_id="ORDER-002",
        sku="LAPTOP-01",
        quantity=2,
    )

    assert inventory.get_reserved_stock("LAPTOP-01") == 5
    assert inventory.get_available_stock("LAPTOP-01") == 5


def test_overselling_is_rejected():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    inventory.reserve(
        reservation_id="ORDER-001",
        sku="LAPTOP-01",
        quantity=7,
    )

    with pytest.raises(ValueError):
        inventory.reserve(
            reservation_id="ORDER-002",
            sku="LAPTOP-01",
            quantity=4,
        )


def test_release_reservation_increases_available_stock():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    inventory.reserve(
        reservation_id="ORDER-001",
        sku="LAPTOP-01",
        quantity=3,
    )

    inventory.release_reservation("ORDER-001")

    assert inventory.get_reserved_stock("LAPTOP-01") == 0
    assert inventory.get_available_stock("LAPTOP-01") == 10


def test_release_only_removes_requested_reservation():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    inventory.reserve(
        reservation_id="ORDER-001",
        sku="LAPTOP-01",
        quantity=3,
    )

    inventory.reserve(
        reservation_id="ORDER-002",
        sku="LAPTOP-01",
        quantity=2,
    )

    inventory.release_reservation("ORDER-001")

    assert inventory.get_reserved_stock("LAPTOP-01") == 2
    assert inventory.get_available_stock("LAPTOP-01") == 8


def test_invalid_sku_is_rejected():
    inventory = Inventory(create_warehouse())

    with pytest.raises(ValueError):
        inventory.get_physical_stock("")


def test_reservation_quantity_must_be_positive():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    with pytest.raises(ValueError):
        inventory.reserve(
            reservation_id="ORDER-001",
            sku="LAPTOP-01",
            quantity=0,
        )


def test_unknown_reservation_cannot_be_released():
    inventory = Inventory(create_warehouse())

    with pytest.raises(ValueError):
        inventory.release_reservation("ORDER-999")


def test_duplicate_reservation_id_is_rejected():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    inventory.reserve(
        reservation_id="ORDER-001",
        sku="LAPTOP-01",
        quantity=3,
    )

    with pytest.raises(ValueError):
        inventory.reserve(
            reservation_id="ORDER-001",
            sku="LAPTOP-01",
            quantity=2,
        )


def test_reservation_quantity_must_be_integer():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    with pytest.raises(ValueError):
        inventory.reserve(
            reservation_id="ORDER-001",
            sku="LAPTOP-01",
            quantity=2.5,
        )


def test_boolean_reservation_quantity_is_rejected():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    with pytest.raises(ValueError):
        inventory.reserve(
            reservation_id="ORDER-001",
            sku="LAPTOP-01",
            quantity=True,
        )