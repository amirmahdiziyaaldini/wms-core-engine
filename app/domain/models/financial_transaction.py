from datetime import datetime
from decimal import Decimal

from app.domain.enums.financial_transaction_type import (
    FinancialTransactionType,
)


class FinancialTransaction:

    def __init__(
        self,
        transaction_id: str,
        return_id: str,
        order_id: str,
        amount: Decimal,
        transaction_type: FinancialTransactionType,
        timestamp: datetime | None = None,
    ):
        if not isinstance(transaction_id, str):
            raise ValueError(
                "Transaction ID must be a string"
            )

        if not transaction_id.strip():
            raise ValueError(
                "Transaction ID cannot be empty"
            )

        if not isinstance(return_id, str):
            raise ValueError(
                "Return ID must be a string"
            )

        if not return_id.strip():
            raise ValueError(
                "Return ID cannot be empty"
            )

        if not isinstance(order_id, str):
            raise ValueError(
                "Order ID must be a string"
            )

        if not order_id.strip():
            raise ValueError(
                "Order ID cannot be empty"
            )

        if not isinstance(amount, Decimal):
            raise ValueError(
                "Amount must be a Decimal"
            )

        if amount <= Decimal("0"):
            raise ValueError(
                "Amount must be positive"
            )

        if not isinstance(
            transaction_type,
            FinancialTransactionType,
        ):
            raise ValueError(
                "Transaction type must be a FinancialTransactionType"
            )

        if timestamp is not None:
            if not isinstance(timestamp, datetime):
                raise ValueError(
                    "Timestamp must be a datetime"
                )

        self.transaction_id = transaction_id
        self.return_id = return_id
        self.order_id = order_id
        self.amount = amount
        self.type = transaction_type
        self.timestamp = (
            timestamp
            if timestamp is not None
            else datetime.now()
        )