import pytest
from datetime import date
from decimal import Decimal

from app.domain.models.base_product import BaseProduct
from app.domain.models.batch import Batch
from app.domain.models.inventory import Inventory
from app.domain.models.reservation import Reservation
from app.domain.models.warehouse import Warehouse
from app.domain.enums.warehouse_type import WarehouseType


def create_product(sku="LAPTOP-01"):
    return BaseProduct(
        sku=sku,
        name="Laptop",
        barcode="123456789",
        category="Electronics",
        base_price=Decimal("500000"),
    )


def create_warehouse():
    return Warehouse(
        warehouse_id="WH-001",
        name="Central Warehouse",
        location="Tehran",
        warehouse_type=WarehouseType.CENTRAL,
    )


def create_batch(
    quantity=10,
    sku="LAPTOP-01",
    batch_id="BATCH-001",
):
    return Batch(
        batch_id=batch_id,
        product=create_product(sku),
        quantity=quantity,
        entry_date=date(2026, 9, 1),
    )


def test_add_batch():
    inventory = Inventory(create_warehouse())

    batch = create_batch()

    inventory.add_batch(batch)

    assert inventory.batches == [batch]


def test_add_batch_requires_batch_instance():
    inventory = Inventory(create_warehouse())

    with pytest.raises(ValueError):
        inventory.add_batch("invalid")


def test_physical_stock_returns_total_quantity_for_sku():
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
            quantity=20,
            batch_id="BATCH-002",
        )
    )

    assert inventory.get_physical_stock("LAPTOP-01") == 30


def test_physical_stock_ignores_other_skus():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(
            quantity=10,
            sku="LAPTOP-01",
            batch_id="BATCH-001",
        )
    )

    inventory.add_batch(
        create_batch(
            quantity=20,
            sku="PHONE-01",
            batch_id="BATCH-002",
        )
    )

    assert inventory.get_physical_stock("LAPTOP-01") == 10
    assert inventory.get_physical_stock("PHONE-01") == 20


def test_physical_stock_requires_string_sku():
    inventory = Inventory(create_warehouse())

    with pytest.raises(ValueError):
        inventory.get_physical_stock(123)


def test_physical_stock_rejects_empty_sku():
    inventory = Inventory(create_warehouse())

    with pytest.raises(ValueError):
        inventory.get_physical_stock("")


def test_reserved_stock_is_zero_without_reservations():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    assert inventory.get_reserved_stock("LAPTOP-01") == 0


def test_available_stock_equals_physical_stock_without_reservations():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    assert inventory.get_available_stock("LAPTOP-01") == 10


def test_reservation_does_not_reduce_physical_stock():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    reservation = Reservation(
        reservation_id="RES-001",
        order_id="ORD-001",
        order_item_id="ITEM-001",
        sku="LAPTOP-01",
        quantity=4,
    )

    inventory.reserve_reservation(reservation)

    assert inventory.get_physical_stock("LAPTOP-01") == 10


def test_multiple_reservations_are_combined():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    reservation_1 = Reservation(
        reservation_id="RES-001",
        order_id="ORD-001",
        order_item_id="ITEM-001",
        sku="LAPTOP-01",
        quantity=3,
    )

    reservation_2 = Reservation(
        reservation_id="RES-002",
        order_id="ORD-002",
        order_item_id="ITEM-002",
        sku="LAPTOP-01",
        quantity=2,
    )

    inventory.reserve_reservation(reservation_1)
    inventory.reserve_reservation(reservation_2)

    assert inventory.get_reserved_stock("LAPTOP-01") == 5
    assert inventory.get_available_stock("LAPTOP-01") == 5


def test_overselling_is_rejected():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    reservation = Reservation(
        reservation_id="RES-001",
        order_id="ORD-001",
        order_item_id="ITEM-001",
        sku="LAPTOP-01",
        quantity=10,
    )

    inventory.reserve_reservation(reservation)

    with pytest.raises(ValueError):
        inventory.reserve(
            reservation_id="RES-002",
            sku="LAPTOP-01",
            quantity=1,
        )


def test_release_reservation_increases_available_stock():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    reservation = Reservation(
        reservation_id="RES-001",
        order_id="ORD-001",
        order_item_id="ITEM-001",
        sku="LAPTOP-01",
        quantity=4,
    )

    inventory.reserve_reservation(reservation)

    assert inventory.get_available_stock("LAPTOP-01") == 6

    inventory.release_reservation("RES-001")

    assert inventory.get_reserved_stock("LAPTOP-01") == 0
    assert inventory.get_available_stock("LAPTOP-01") == 10


def test_release_only_removes_requested_reservation():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    reservation_1 = Reservation(
        reservation_id="RES-001",
        order_id="ORD-001",
        order_item_id="ITEM-001",
        sku="LAPTOP-01",
        quantity=3,
    )

    reservation_2 = Reservation(
        reservation_id="RES-002",
        order_id="ORD-002",
        order_item_id="ITEM-002",
        sku="LAPTOP-01",
        quantity=2,
    )

    inventory.reserve_reservation(reservation_1)
    inventory.reserve_reservation(reservation_2)

    inventory.release_reservation("RES-001")

    assert inventory.get_reserved_stock("LAPTOP-01") == 2
    assert inventory.get_available_stock("LAPTOP-01") == 8


def test_release_invalid_reservation_id_is_rejected():
    inventory = Inventory(create_warehouse())

    with pytest.raises(ValueError):
        inventory.release_reservation("RES-999")


def test_reserve_rejects_empty_reservation_id():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    with pytest.raises(ValueError):
        inventory.reserve(
            reservation_id="",
            sku="LAPTOP-01",
            quantity=1,
        )


def test_reserve_rejects_empty_sku():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    with pytest.raises(ValueError):
        inventory.reserve(
            reservation_id="RES-001",
            sku="",
            quantity=1,
        )


def test_reserve_rejects_non_positive_quantity():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    with pytest.raises(ValueError):
        inventory.reserve(
            reservation_id="RES-001",
            sku="LAPTOP-01",
            quantity=0,
        )


def test_reserve_rejects_non_integer_quantity():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    with pytest.raises(ValueError):
        inventory.reserve(
            reservation_id="RES-001",
            sku="LAPTOP-01",
            quantity=2.5,
        )


def test_reserve_rejects_boolean_quantity():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    with pytest.raises(ValueError):
        inventory.reserve(
            reservation_id="RES-001",
            sku="LAPTOP-01",
            quantity=True,
        )


def test_duplicate_reservation_id_is_rejected():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    reservation = Reservation(
        reservation_id="RES-001",
        order_id="ORD-001",
        order_item_id="ITEM-001",
        sku="LAPTOP-01",
        quantity=2,
    )

    inventory.reserve_reservation(reservation)

    with pytest.raises(ValueError):
        inventory.reserve_reservation(reservation)


def test_reservation_quantity_must_be_positive():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    with pytest.raises(ValueError):
        Reservation(
            reservation_id="RES-001",
            order_id="ORD-001",
            order_item_id="ITEM-001",
            sku="LAPTOP-01",
            quantity=0,
        )


def test_reservation_quantity_must_be_integer():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    with pytest.raises(ValueError):
        Reservation(
            reservation_id="RES-001",
            order_id="ORD-001",
            order_item_id="ITEM-001",
            sku="LAPTOP-01",
            quantity=2.5,
        )


def test_boolean_reservation_quantity_is_rejected():
    inventory = Inventory(create_warehouse())

    inventory.add_batch(
        create_batch(quantity=10)
    )

    with pytest.raises(ValueError):
        Reservation(
            reservation_id="RES-001",
            order_id="ORD-001",
            order_item_id="ITEM-001",
            sku="LAPTOP-01",
            quantity=True,
        )