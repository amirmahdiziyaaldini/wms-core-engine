from app.domain.models.payment_transaction import PaymentTransaction


class PaymentTransactionRepository:

    def __init__(self):
        self._transactions: dict[
            str,
            PaymentTransaction,
        ] = {}

    def save(
        self,
        transaction: PaymentTransaction,
    ) -> None:
        if not isinstance(
            transaction,
            PaymentTransaction,
        ):
            raise ValueError(
                "Transaction must be a PaymentTransaction"
            )

        if transaction.transaction_id in self._transactions:
            raise ValueError(
                f"Transaction already exists: "
                f"{transaction.transaction_id}"
            )

        for existing_transaction in self._transactions.values():
            if (
                existing_transaction.reference
                == transaction.reference
            ):
                raise ValueError(
                    "Payment reference already exists"
                )

        self._transactions[
            transaction.transaction_id
        ] = transaction

    def get(
        self,
        transaction_id: str,
    ) -> PaymentTransaction | None:
        if not isinstance(transaction_id, str):
            raise ValueError(
                "Transaction ID must be a string"
            )

        return self._transactions.get(
            transaction_id
        )

    def get_by_order_id(
        self,
        order_id: str,
    ) -> list[PaymentTransaction]:
        if not isinstance(order_id, str):
            raise ValueError(
                "Order ID must be a string"
            )

        return [
            transaction
            for transaction in self._transactions.values()
            if transaction.order_id == order_id
        ]

    def get_by_reference(
        self,
        reference: str,
    ) -> PaymentTransaction | None:
        if not isinstance(reference, str):
            raise ValueError(
                "Payment reference must be a string"
            )

        for transaction in self._transactions.values():
            if transaction.reference == reference:
                return transaction

        return None

    def list_all(
        self,
    ) -> list[PaymentTransaction]:
        return list(
            self._transactions.values()
        )