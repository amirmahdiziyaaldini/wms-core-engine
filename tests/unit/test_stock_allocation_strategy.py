from datetime import date
from decimal import Decimal

import pytest

from app.domain.models.base_product import BaseProduct
from app.domain.models.batch import Batch
from app.strategies.fifo_stock_allocation_strategy import (
    FIFOStockAllocationStrategy,
)
from app.strategies.lifo_stock_allocation_strategy import (
    LIFOStockAllocationStrategy,
)


def create_product():
    return BaseProduct(
        sku="LAPTOP-01",
        name="Laptop",
        barcode="123456789",
        category="Electronics",
        base_price=Decimal("1000"),
    )


def create_batch(
    batch_id,
    quantity,
    entry_date,
    expiry_date=None,
):
    return Batch(
        batch_id=batch_id,
        product=create_product(),
        quantity=quantity,
        entry_date=entry_date,
        expiry_date=expiry_date,
    )


def test_fifo_selects_oldest_batch_first():
    strategy = FIFOStockAllocationStrategy()

    batches = [
        create_batch("B-003", 10, date(2026, 9, 10)),
        create_batch("B-001", 10, date(2026, 9, 1)),
        create_batch("B-002", 10, date(2026, 9, 5)),
    ]

    result = strategy.allocate(batches, 5)

    assert result == {
        "B-001": 5,
    }


def test_lifo_selects_newest_batch_first():
    strategy = LIFOStockAllocationStrategy()

    batches = [
        create_batch("B-001", 10, date(2026, 9, 1)),
        create_batch("B-003", 10, date(2026, 9, 10)),
        create_batch("B-002", 10, date(2026, 9, 5)),
    ]

    result = strategy.allocate(batches, 5)

    assert result == {
        "B-003": 5,
    }


def test_fifo_splits_allocation_across_multiple_batches():
    strategy = FIFOStockAllocationStrategy()

    batches = [
        create_batch("B-001", 4, date(2026, 9, 1)),
        create_batch("B-002", 7, date(2026, 9, 5)),
        create_batch("B-003", 10, date(2026, 9, 10)),
    ]

    result = strategy.allocate(batches, 12)

    assert result == {
        "B-001": 4,
        "B-002": 7,
        "B-003": 1,
    }


def test_lifo_splits_allocation_across_multiple_batches():
    strategy = LIFOStockAllocationStrategy()

    batches = [
        create_batch("B-001", 4, date(2026, 9, 1)),
        create_batch("B-002", 7, date(2026, 9, 5)),
        create_batch("B-003", 10, date(2026, 9, 10)),
    ]

    result = strategy.allocate(batches, 12)

    assert result == {
        "B-003": 10,
        "B-002": 2,
    }


def test_fifo_skips_empty_batches():
    strategy = FIFOStockAllocationStrategy()

    empty_batch = create_batch(
        "B-001",
        1,
        date(2026, 9, 1),
    )
    empty_batch.quantity = 0

    batches = [
        empty_batch,
        create_batch("B-002", 10, date(2026, 9, 5)),
    ]

    result = strategy.allocate(batches, 5)

    assert result == {
        "B-002": 5,
    }


def test_lifo_skips_empty_batches():
    strategy = LIFOStockAllocationStrategy()

    empty_batch = create_batch(
        "B-002",
        1,
        date(2026, 9, 10),
    )
    empty_batch.quantity = 0

    batches = [
        create_batch("B-001", 10, date(2026, 9, 1)),
        empty_batch,
    ]

    result = strategy.allocate(batches, 5)

    assert result == {
        "B-001": 5,
    }


def test_fifo_skips_expired_batches():
    strategy = FIFOStockAllocationStrategy()

    batches = [
        create_batch(
            "B-001",
            10,
            date(2026, 9, 1),
            date(2026, 9, 10),
        ),
        create_batch(
            "B-002",
            10,
            date(2026, 9, 5),
            date(2026, 12, 1),
        ),
    ]

    result = strategy.allocate(
        batches,
        5,
        reference_date=date(2026, 9, 20),
    )

    assert result == {
        "B-002": 5,
    }


def test_lifo_skips_expired_batches():
    strategy = LIFOStockAllocationStrategy()

    batches = [
        create_batch(
            "B-001",
            10,
            date(2026, 9, 1),
            date(2026, 12, 1),
        ),
        create_batch(
            "B-002",
            10,
            date(2026, 9, 10),
            date(2026, 9, 15),
        ),
    ]

    result = strategy.allocate(
        batches,
        5,
        reference_date=date(2026, 9, 20),
    )

    assert result == {
        "B-001": 5,
    }


def test_fifo_raises_error_when_valid_stock_is_insufficient():
    strategy = FIFOStockAllocationStrategy()

    batches = [
        create_batch("B-001", 3, date(2026, 9, 1)),
        create_batch("B-002", 2, date(2026, 9, 5)),
    ]

    with pytest.raises(
        ValueError,
        match="Insufficient valid stock",
    ):
        strategy.allocate(batches, 10)


def test_lifo_raises_error_when_valid_stock_is_insufficient():
    strategy = LIFOStockAllocationStrategy()

    batches = [
        create_batch("B-001", 3, date(2026, 9, 1)),
        create_batch("B-002", 2, date(2026, 9, 5)),
    ]

    with pytest.raises(
        ValueError,
        match="Insufficient valid stock",
    ):
        strategy.allocate(batches, 10)


def test_fifo_rejects_invalid_quantity():
    strategy = FIFOStockAllocationStrategy()

    batches = [
        create_batch("B-001", 10, date(2026, 9, 1)),
    ]

    with pytest.raises(
        ValueError,
        match="Quantity must be greater than zero",
    ):
        strategy.allocate(batches, 0)


def test_lifo_rejects_invalid_quantity():
    strategy = LIFOStockAllocationStrategy()

    batches = [
        create_batch("B-001", 10, date(2026, 9, 1)),
    ]

    with pytest.raises(
        ValueError,
        match="Quantity must be greater than zero",
    ):
        strategy.allocate(batches, 0)