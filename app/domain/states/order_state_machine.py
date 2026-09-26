from datetime import datetime

from app.domain.enums.order_status import OrderStatus
from app.domain.models.order import Order


class OrderStateMachine:
    _TRANSITIONS = {
        OrderStatus.CREATED: {
            OrderStatus.PAID,
            OrderStatus.RESERVED,
            OrderStatus.CANCELLED,
        },
        OrderStatus.RESERVED: {
            OrderStatus.CREATED,
            OrderStatus.PAID,
            OrderStatus.CANCELLED,
        },
        OrderStatus.PAID: {
            OrderStatus.SHIPPED,
            OrderStatus.CANCELLED,
        },
        OrderStatus.SHIPPED: {
            OrderStatus.DELIVERED,
        },
        OrderStatus.DELIVERED: set(),
        OrderStatus.CANCELLED: set(),
    }

    def can_transition(
        self,
        current_status: OrderStatus,
        target_status: OrderStatus,
    ) -> bool:
        if not isinstance(current_status, OrderStatus):
            raise ValueError(
                "Current status must be an OrderStatus"
            )

        if not isinstance(target_status, OrderStatus):
            raise ValueError(
                "Target status must be an OrderStatus"
            )

        allowed_statuses = self._TRANSITIONS.get(
            current_status,
            set(),
        )

        return target_status in allowed_statuses

    def transition(
        self,
        order: Order,
        target_status: OrderStatus,
        timestamp: datetime | None = None,
    ) -> None:
        if not isinstance(order, Order):
            raise ValueError(
                "Order must be an Order"
            )

        if not isinstance(target_status, OrderStatus):
            raise ValueError(
                "Target status must be an OrderStatus"
            )

        if not self.can_transition(
            order.status,
            target_status,
        ):
            raise ValueError(
                f"Invalid order transition: "
                f"{order.status.value} -> "
                f"{target_status.value}"
            )

        if timestamp is None:
            timestamp = datetime.now()

        if not isinstance(timestamp, datetime):
            raise ValueError(
                "Timestamp must be a datetime"
            )

        order._set_status(
            target_status,
            timestamp,
        )