from app.domain.models.financial_transaction import (
    FinancialTransaction,
)


class FinancialTransactionRepository:

    def __init__(self):
        self._transactions: dict[
            str,
            FinancialTransaction,
        ] = {}

    def save(
        self,
        transaction: FinancialTransaction,
    ) -> None:
        if not isinstance(
            transaction,
            FinancialTransaction,
        ):
            raise ValueError(
                "Transaction must be a FinancialTransaction"
            )

        if transaction.transaction_id in self._transactions:
            raise ValueError(
                f"Transaction already exists: "
                f"{transaction.transaction_id}"
            )

        for existing_transaction in self._transactions.values():
            if (
                existing_transaction.return_id
                == transaction.return_id
            ):
                raise ValueError(
                    "Refund already exists for this return"
                )

        self._transactions[
            transaction.transaction_id
        ] = transaction

    def get(
        self,
        transaction_id: str,
    ) -> FinancialTransaction | None:
        if not isinstance(transaction_id, str):
            raise ValueError(
                "Transaction ID must be a string"
            )

        return self._transactions.get(
            transaction_id
        )

    def get_by_return_id(
        self,
        return_id: str,
    ) -> FinancialTransaction | None:
        if not isinstance(return_id, str):
            raise ValueError(
                "Return ID must be a string"
            )

        for transaction in self._transactions.values():
            if transaction.return_id == return_id:
                return transaction

        return None

    def get_by_order_id(
        self,
        order_id: str,
    ) -> list[FinancialTransaction]:
        if not isinstance(order_id, str):
            raise ValueError(
                "Order ID must be a string"
            )

        return [
            transaction
            for transaction in self._transactions.values()
            if transaction.order_id == order_id
        ]

    def list_all(
        self,
    ) -> list[FinancialTransaction]:
        return list(
            self._transactions.values()
        )