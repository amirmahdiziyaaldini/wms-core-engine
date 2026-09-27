from decimal import Decimal

from app.domain.enums.financial_transaction_type import (
    FinancialTransactionType,
)
from app.domain.models.financial_transaction import (
    FinancialTransaction,
)
from app.domain.models.payment_transaction import (
    PaymentTransaction,
)
from app.repositories.financial_transaction_repository import (
    FinancialTransactionRepository,
)
from app.repositories.payment_transaction_repository import (
    PaymentTransactionRepository,
)


def test_payment_repository_only_stores_duplicate_reference():
    repository = PaymentTransactionRepository()

    first = PaymentTransaction(
        transaction_id="PAY-001",
        order_id="ORD-001",
        reference="REF-001",
        amount=Decimal("100"),
    )

    second = PaymentTransaction(
        transaction_id="PAY-002",
        order_id="ORD-002",
        reference="REF-001",
        amount=Decimal("200"),
    )

    repository.save(first)
    repository.save(second)

    assert repository.list_all() == [
        first,
        second,
    ]


def test_financial_repository_only_stores_duplicate_return():
    repository = FinancialTransactionRepository()

    first = FinancialTransaction(
        transaction_id="REF-001",
        return_id="RET-001",
        order_id="ORD-001",
        amount=Decimal("100"),
        transaction_type=FinancialTransactionType.REFUND,
    )

    second = FinancialTransaction(
        transaction_id="REF-002",
        return_id="RET-001",
        order_id="ORD-001",
        amount=Decimal("100"),
        transaction_type=FinancialTransactionType.REFUND,
    )

    repository.save(first)
    repository.save(second)

    assert repository.list_all() == [
        first,
        second,
    ]