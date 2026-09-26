from datetime import datetime
from decimal import Decimal

import pytest

from app.domain.enums.financial_transaction_type import (
    FinancialTransactionType,
)
from app.domain.models.financial_transaction import (
    FinancialTransaction,
)
from app.repositories.financial_transaction_repository import (
    FinancialTransactionRepository,
)


def test_financial_transaction_creation():
    timestamp = datetime(2026, 9, 26, 14, 0)

    transaction = FinancialTransaction(
        transaction_id="REF-001",
        return_id="RET-001",
        order_id="ORD-001",
        amount=Decimal("500000"),
        transaction_type=FinancialTransactionType.REFUND,
        timestamp=timestamp,
    )

    assert transaction.transaction_id == "REF-001"
    assert transaction.return_id == "RET-001"
    assert transaction.order_id == "ORD-001"
    assert transaction.amount == Decimal("500000")
    assert transaction.type == FinancialTransactionType.REFUND
    assert transaction.timestamp == timestamp


def test_financial_transaction_default_timestamp():
    transaction = FinancialTransaction(
        transaction_id="REF-002",
        return_id="RET-002",
        order_id="ORD-002",
        amount=Decimal("250000"),
        transaction_type=FinancialTransactionType.REFUND,
    )

    assert isinstance(transaction.timestamp, datetime)


def test_financial_transaction_rejects_empty_transaction_id():
    with pytest.raises(ValueError):
        FinancialTransaction(
            transaction_id="",
            return_id="RET-001",
            order_id="ORD-001",
            amount=Decimal("500000"),
            transaction_type=FinancialTransactionType.REFUND,
        )


def test_financial_transaction_rejects_empty_return_id():
    with pytest.raises(ValueError):
        FinancialTransaction(
            transaction_id="REF-001",
            return_id="",
            order_id="ORD-001",
            amount=Decimal("500000"),
            transaction_type=FinancialTransactionType.REFUND,
        )


def test_financial_transaction_rejects_empty_order_id():
    with pytest.raises(ValueError):
        FinancialTransaction(
            transaction_id="REF-001",
            return_id="RET-001",
            order_id="",
            amount=Decimal("500000"),
            transaction_type=FinancialTransactionType.REFUND,
        )


def test_financial_transaction_rejects_non_decimal_amount():
    with pytest.raises(ValueError):
        FinancialTransaction(
            transaction_id="REF-001",
            return_id="RET-001",
            order_id="ORD-001",
            amount=500000,
            transaction_type=FinancialTransactionType.REFUND,
        )


def test_financial_transaction_rejects_non_positive_amount():
    with pytest.raises(ValueError):
        FinancialTransaction(
            transaction_id="REF-001",
            return_id="RET-001",
            order_id="ORD-001",
            amount=Decimal("0"),
            transaction_type=FinancialTransactionType.REFUND,
        )


def test_financial_transaction_repository_save_and_get():
    repository = FinancialTransactionRepository()

    transaction = FinancialTransaction(
        transaction_id="REF-001",
        return_id="RET-001",
        order_id="ORD-001",
        amount=Decimal("500000"),
        transaction_type=FinancialTransactionType.REFUND,
    )

    repository.save(transaction)

    assert repository.get("REF-001") is transaction


def test_financial_transaction_repository_get_by_return_id():
    repository = FinancialTransactionRepository()

    transaction = FinancialTransaction(
        transaction_id="REF-001",
        return_id="RET-001",
        order_id="ORD-001",
        amount=Decimal("500000"),
        transaction_type=FinancialTransactionType.REFUND,
    )

    repository.save(transaction)

    result = repository.get_by_return_id("RET-001")

    assert result is transaction


def test_financial_transaction_repository_get_by_order_id():
    repository = FinancialTransactionRepository()

    transaction_1 = FinancialTransaction(
        transaction_id="REF-001",
        return_id="RET-001",
        order_id="ORD-001",
        amount=Decimal("500000"),
        transaction_type=FinancialTransactionType.REFUND,
    )

    transaction_2 = FinancialTransaction(
        transaction_id="REF-002",
        return_id="RET-002",
        order_id="ORD-001",
        amount=Decimal("250000"),
        transaction_type=FinancialTransactionType.REFUND,
    )

    repository.save(transaction_1)
    repository.save(transaction_2)

    result = repository.get_by_order_id("ORD-001")

    assert result == [transaction_1, transaction_2]


def test_financial_transaction_repository_rejects_duplicate_transaction_id():
    repository = FinancialTransactionRepository()

    transaction_1 = FinancialTransaction(
        transaction_id="REF-001",
        return_id="RET-001",
        order_id="ORD-001",
        amount=Decimal("500000"),
        transaction_type=FinancialTransactionType.REFUND,
    )

    transaction_2 = FinancialTransaction(
        transaction_id="REF-001",
        return_id="RET-002",
        order_id="ORD-002",
        amount=Decimal("250000"),
        transaction_type=FinancialTransactionType.REFUND,
    )

    repository.save(transaction_1)

    with pytest.raises(ValueError):
        repository.save(transaction_2)


def test_financial_transaction_repository_rejects_duplicate_return():
    repository = FinancialTransactionRepository()

    transaction_1 = FinancialTransaction(
        transaction_id="REF-001",
        return_id="RET-001",
        order_id="ORD-001",
        amount=Decimal("500000"),
        transaction_type=FinancialTransactionType.REFUND,
    )

    transaction_2 = FinancialTransaction(
        transaction_id="REF-002",
        return_id="RET-001",
        order_id="ORD-001",
        amount=Decimal("250000"),
        transaction_type=FinancialTransactionType.REFUND,
    )

    repository.save(transaction_1)

    with pytest.raises(ValueError):
        repository.save(transaction_2)


def test_financial_transaction_repository_list_all():
    repository = FinancialTransactionRepository()

    transaction = FinancialTransaction(
        transaction_id="REF-001",
        return_id="RET-001",
        order_id="ORD-001",
        amount=Decimal("500000"),
        transaction_type=FinancialTransactionType.REFUND,
    )

    repository.save(transaction)

    assert repository.list_all() == [transaction]