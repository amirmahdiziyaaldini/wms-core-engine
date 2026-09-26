from datetime import datetime
from decimal import Decimal

from app.domain.enums.financial_transaction_type import (
    FinancialTransactionType,
)
from app.domain.enums.return_status import ReturnStatus
from app.domain.models.financial_transaction import (
    FinancialTransaction,
)
from app.domain.models.order import Order
from app.domain.models.return_request import ReturnRequest
from app.domain.states.return_state_machine import ReturnStateMachine
from app.repositories.financial_transaction_repository import (
    FinancialTransactionRepository,
)


class RefundService:
    def __init__(
        self,
        financial_transaction_repository: (
            FinancialTransactionRepository | None
        ) = None,
        return_state_machine: ReturnStateMachine | None = None,
    ):
        if financial_transaction_repository is not None:
            if not isinstance(
                financial_transaction_repository,
                FinancialTransactionRepository,
            ):
                raise ValueError(
                    "Financial transaction repository must be a "
                    "FinancialTransactionRepository"
                )

        if return_state_machine is not None:
            if not isinstance(
                return_state_machine,
                ReturnStateMachine,
            ):
                raise ValueError(
                    "Return state machine must be a ReturnStateMachine"
                )

        self.financial_transaction_repository = (
            financial_transaction_repository
            if financial_transaction_repository is not None
            else FinancialTransactionRepository()
        )

        self.return_state_machine = (
            return_state_machine
            if return_state_machine is not None
            else ReturnStateMachine()
        )

    def refund(
        self,
        return_request: ReturnRequest,
        order: Order,
        timestamp: datetime | None = None,
    ) -> FinancialTransaction:
        if not isinstance(
            return_request,
            ReturnRequest,
        ):
            raise ValueError(
                "Return request must be a ReturnRequest"
            )

        if not isinstance(order, Order):
            raise ValueError(
                "Order must be an Order"
            )

        if return_request.order_id != order.order_id:
            raise ValueError(
                "Return request does not belong to the order"
            )

        if return_request.status != ReturnStatus.APPROVED:
            raise ValueError(
                "Only approved returns can be refunded"
            )

        existing_transaction = (
            self.financial_transaction_repository.get_by_return_id(
                return_request.return_id
            )
        )

        if existing_transaction is not None:
            raise ValueError(
                "Refund already exists for this return"
            )

        if timestamp is None:
            timestamp = datetime.now()

        if not isinstance(timestamp, datetime):
            raise ValueError(
                "Timestamp must be a datetime"
            )

        amount = self._calculate_refund_amount(
            return_request=return_request,
            order=order,
        )

        transaction_id = (
            f"REFUND-{return_request.return_id}"
        )

        transaction = FinancialTransaction(
            transaction_id=transaction_id,
            return_id=return_request.return_id,
            order_id=order.order_id,
            amount=amount,
            transaction_type=FinancialTransactionType.REFUND,
            timestamp=timestamp,
        )

        self.financial_transaction_repository.save(
            transaction
        )

        self.return_state_machine.transition(
            return_request,
            ReturnStatus.REFUNDED,
            timestamp=timestamp,
        )

        return transaction

    def _calculate_refund_amount(
        self,
        return_request: ReturnRequest,
        order: Order,
    ) -> Decimal:
        order_items = {
            item.sku: item
            for item in order.items
        }

        total = Decimal("0")

        for return_item in return_request.items:
            if return_item.sku not in order_items:
                raise ValueError(
                    f"SKU {return_item.sku} is not part of the order"
                )

            order_item = order_items[
                return_item.sku
            ]

            if order_item.unit_price is None:
                raise ValueError(
                    f"Price snapshot is missing for SKU "
                    f"{return_item.sku}"
                )

            if return_item.quantity > order_item.quantity:
                raise ValueError(
                    f"Return quantity for SKU "
                    f"{return_item.sku} exceeds order quantity"
                )

            total += (
                order_item.unit_price
                * return_item.quantity
            )

        if total <= Decimal("0"):
            raise ValueError(
                "Refund amount must be positive"
            )

        return total