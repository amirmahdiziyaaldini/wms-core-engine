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
        if not isinstance(
            current_status,
            OrderStatus,
        ):
            raise ValueError(
                "Current status must be an OrderStatus"
            )

        if not isinstance(
            target_status,
            OrderStatus,
        ):
            raise ValueError(
                "Target status must be an OrderStatus"
            )

        return target_status in self._TRANSITIONS.get(
            current_status,
            set(),
        )

    def transition(
        self,
        order: Order,
        target_status: OrderStatus,
    ) -> None:
        if not isinstance(order, Order):
            raise ValueError(
                "Order must be an Order instance"
            )

        if not isinstance(
            target_status,
            OrderStatus,
        ):
            raise ValueError(
                "Target status must be an OrderStatus"
            )

        current_status = order.status

        if not self.can_transition(
            current_status,
            target_status,
        ):
            raise ValueError(
                f"Invalid order transition: "
                f"{current_status.value} -> "
                f"{target_status.value}"
            )

        timestamp = datetime.now()

        order._set_status(
            target_status,
            timestamp,
        )