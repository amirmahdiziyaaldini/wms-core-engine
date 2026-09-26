from datetime import datetime

from app.domain.enums.return_reason import ReturnReason
from app.domain.enums.return_status import ReturnStatus
from app.domain.models.order import Order
from app.domain.models.return_item import ReturnItem


class ReturnRequest:

    def __init__(
        self,
        return_id: str,
        order: Order,
        reason: ReturnReason,
        items: list[ReturnItem],
        status: ReturnStatus = ReturnStatus.REQUESTED,
        requested_at: datetime | None = None,
        previous_returns: list["ReturnRequest"] | None = None,
    ):
        if not isinstance(return_id, str):
            raise ValueError("Return ID must be a string")

        if not return_id.strip():
            raise ValueError("Return ID cannot be empty")

        if not isinstance(order, Order):
            raise ValueError("Order must be an Order")

        if not isinstance(reason, ReturnReason):
            raise ValueError("Reason must be a ReturnReason")

        if not isinstance(status, ReturnStatus):
            raise ValueError("Status must be a ReturnStatus")

        if status != ReturnStatus.REQUESTED:
            raise ValueError(
                "Return request must start with REQUESTED"
            )

        if requested_at is not None and not isinstance(
            requested_at,
            datetime,
        ):
            raise ValueError("Requested at must be a datetime")

        if not isinstance(items, list):
            raise ValueError("Items must be a list")

        if not items:
            raise ValueError(
                "Return request must contain at least one item"
            )

        for item in items:
            if not isinstance(item, ReturnItem):
                raise ValueError(
                    "All items must be ReturnItem instances"
                )

        if previous_returns is None:
            previous_returns = []

        if not isinstance(previous_returns, list):
            raise ValueError(
                "Previous returns must be a list"
            )

        for previous_return in previous_returns:
            if not isinstance(
                previous_return,
                ReturnRequest,
            ):
                raise ValueError(
                    "All previous returns must be ReturnRequest instances"
                )

            if previous_return.order_id != order.order_id:
                raise ValueError(
                    "Previous return must belong to the same order"
                )

            if previous_return.return_id == return_id:
                raise ValueError(
                    "Return ID must be unique"
                )

        order_quantities: dict[str, int] = {}

        for order_item in order.items:
            order_quantities[order_item.sku] = (
                order_quantities.get(order_item.sku, 0)
                + order_item.quantity
            )

        previous_quantities: dict[str, int] = {}

        for previous_return in previous_returns:
            for previous_item in previous_return.items:
                previous_quantities[previous_item.sku] = (
                    previous_quantities.get(
                        previous_item.sku,
                        0,
                    )
                    + previous_item.quantity
                )

        current_quantities: dict[str, int] = {}

        for item in items:
            current_quantities[item.sku] = (
                current_quantities.get(item.sku, 0)
                + item.quantity
            )

        for sku, quantity in current_quantities.items():
            purchased_quantity = order_quantities.get(sku, 0)

            if purchased_quantity == 0:
                raise ValueError(
                    f"SKU {sku} is not part of the order"
                )

            returned_quantity = (
                previous_quantities.get(sku, 0)
                + quantity
            )

            if returned_quantity > purchased_quantity:
                raise ValueError(
                    f"Return quantity for SKU {sku} exceeds purchased quantity"
                )

        self.return_id = return_id
        self.order_id = order.order_id
        self._status = ReturnStatus.REQUESTED
        self.reason = reason
        self.items = items
        self.requested_at = (
            requested_at
            if requested_at is not None
            else datetime.now()
        )
        self.received_at_warehouse = None
        self.qc_inspection_at = None
        self.approved_at = None
        self.rejected_at = None
        self.refunded_at = None

    @property
    def status(self) -> ReturnStatus:
        return self._status

    def _set_status(
        self,
        status: ReturnStatus,
        timestamp: datetime,
    ) -> None:
        if not isinstance(status, ReturnStatus):
            raise ValueError(
                "Status must be a ReturnStatus"
            )

        if not isinstance(timestamp, datetime):
            raise ValueError(
                "Timestamp must be a datetime"
            )

        self._status = status

        if status == ReturnStatus.RECEIVED_AT_WAREHOUSE:
            self.received_at_warehouse = timestamp

        elif status == ReturnStatus.QC_INSPECTION:
            self.qc_inspection_at = timestamp

        elif status == ReturnStatus.APPROVED:
            self.approved_at = timestamp

        elif status == ReturnStatus.REJECTED:
            self.rejected_at = timestamp

        elif status == ReturnStatus.REFUNDED:
            self.refunded_at = timestamp