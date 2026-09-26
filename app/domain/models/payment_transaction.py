from datetime import datetime
from decimal import Decimal


class PaymentTransaction:

    def __init__(
        self,
        transaction_id: str,
        order_id: str,
        reference: str,
        amount: Decimal,
        created_at: datetime | None = None,
    ):
        if not isinstance(transaction_id, str):
            raise ValueError(
                "Transaction ID must be a string"
            )

        if not transaction_id.strip():
            raise ValueError(
                "Transaction ID cannot be empty"
            )

        if not isinstance(order_id, str):
            raise ValueError(
                "Order ID must be a string"
            )

        if not order_id.strip():
            raise ValueError(
                "Order ID cannot be empty"
            )

        if not isinstance(reference, str):
            raise ValueError(
                "Payment reference must be a string"
            )

        if not reference.strip():
            raise ValueError(
                "Payment reference cannot be empty"
            )

        if not isinstance(amount, Decimal):
            raise ValueError(
                "Payment amount must be a Decimal"
            )

        if amount <= Decimal("0"):
            raise ValueError(
                "Payment amount must be positive"
            )

        if created_at is not None:
            if not isinstance(created_at, datetime):
                raise ValueError(
                    "Created at must be a datetime"
                )

        self.transaction_id = transaction_id
        self.order_id = order_id
        self.reference = reference
        self.amount = amount
        self.created_at = (
            created_at
            if created_at is not None
            else datetime.now()
        )