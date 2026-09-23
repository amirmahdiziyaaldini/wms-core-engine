import pytest

from app.domain.models.reservation import Reservation


def create_reservation(
    reservation_id="RES-001",
    order_id="ORD-001",
    order_item_id="ITEM-001",
    sku="LAPTOP-01",
    quantity=3,
    batch_allocations=None,
):
    return Reservation(
        reservation_id=reservation_id,
        order_id=order_id,
        order_item_id=order_item_id,
        sku=sku,
        quantity=quantity,
        batch_allocations=batch_allocations,
    )


def test_create_valid_reservation():
    reservation = create_reservation()

    assert reservation.reservation_id == "RES-001"
    assert reservation.order_id == "ORD-001"
    assert reservation.order_item_id == "ITEM-001"
    assert reservation.sku == "LAPTOP-01"
    assert reservation.quantity == 3
    assert reservation.batch_allocations == {}


def test_create_reservation_with_batch_allocations():
    reservation = create_reservation(
        batch_allocations={
            "BATCH-001": 2,
            "BATCH-002": 1,
        }
    )

    assert reservation.batch_allocations == {
        "BATCH-001": 2,
        "BATCH-002": 1,
    }


def test_reservation_id_must_be_string():
    with pytest.raises(ValueError):
        create_reservation(
            reservation_id=123,
        )


def test_reservation_id_cannot_be_empty():
    with pytest.raises(ValueError):
        create_reservation(
            reservation_id="",
        )


def test_reservation_id_cannot_contain_only_whitespace():
    with pytest.raises(ValueError):
        create_reservation(
            reservation_id="   ",
        )


def test_order_id_must_be_string():
    with pytest.raises(ValueError):
        create_reservation(
            order_id=123,
        )


def test_order_id_cannot_be_empty():
    with pytest.raises(ValueError):
        create_reservation(
            order_id="",
        )


def test_order_item_id_must_be_string():
    with pytest.raises(ValueError):
        create_reservation(
            order_item_id=123,
        )


def test_order_item_id_cannot_be_empty():
    with pytest.raises(ValueError):
        create_reservation(
            order_item_id="",
        )


def test_sku_must_be_string():
    with pytest.raises(ValueError):
        create_reservation(
            sku=123,
        )


def test_sku_cannot_be_empty():
    with pytest.raises(ValueError):
        create_reservation(
            sku="",
        )


def test_quantity_must_be_integer():
    with pytest.raises(ValueError):
        create_reservation(
            quantity=2.5,
        )


def test_boolean_quantity_is_rejected():
    with pytest.raises(ValueError):
        create_reservation(
            quantity=True,
        )


def test_quantity_must_be_positive():
    with pytest.raises(ValueError):
        create_reservation(
            quantity=0,
        )


def test_negative_quantity_is_rejected():
    with pytest.raises(ValueError):
        create_reservation(
            quantity=-1,
        )


def test_batch_allocations_must_be_dictionary():
    with pytest.raises(ValueError):
        create_reservation(
            batch_allocations=[],
        )


def test_batch_id_must_be_string():
    with pytest.raises(ValueError):
        create_reservation(
            batch_allocations={
                123: 2,
            },
        )


def test_batch_id_cannot_be_empty():
    with pytest.raises(ValueError):
        create_reservation(
            batch_allocations={
                "": 2,
            },
        )


def test_allocated_quantity_must_be_integer():
    with pytest.raises(ValueError):
        create_reservation(
            batch_allocations={
                "BATCH-001": 1.5,
            },
        )


def test_boolean_allocated_quantity_is_rejected():
    with pytest.raises(ValueError):
        create_reservation(
            batch_allocations={
                "BATCH-001": True,
            },
        )


def test_allocated_quantity_must_be_positive():
    with pytest.raises(ValueError):
        create_reservation(
            batch_allocations={
                "BATCH-001": 0,
            },
        )


def test_total_batch_allocation_cannot_exceed_quantity():
    with pytest.raises(ValueError):
        create_reservation(
            quantity=3,
            batch_allocations={
                "BATCH-001": 2,
                "BATCH-002": 2,
            },
        )


def test_batch_allocations_are_copied():
    allocations = {
        "BATCH-001": 2,
    }

    reservation = create_reservation(
        batch_allocations=allocations,
    )

    allocations["BATCH-002"] = 1

    assert reservation.batch_allocations == {
        "BATCH-001": 2,
    }