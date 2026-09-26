from datetime import datetime, timedelta
from typing import Callable

from app.domain.enums.order_status import OrderStatus
from app.domain.models.order import Order


class ReturnWindowPolicy:

    def __init__(
        self,
        return_window_days: int = 7,
        now_provider: Callable[[], datetime] | None = None,
    ):
        if isinstance(return_window_days, bool) or not isinstance(
            return_window_days,
            int,
        ):
            raise ValueError("Return window days must be an integer")

        if return_window_days < 0:
            raise ValueError("Return window days cannot be negative")

        if now_provider is not None and not callable(now_provider):
            raise ValueError("Now provider must be callable")

        self.return_window_days = return_window_days
        self.now_provider = (
            now_provider
            if now_provider is not None
            else datetime.now
        )

    def validate(self, order: Order) -> None:
        if not isinstance(order, Order):
            raise ValueError("Order must be an Order")

        if order.status != OrderStatus.DELIVERED:
            raise ValueError(
                "Only delivered orders can be returned"
            )

        if order.delivered_at is None:
            raise ValueError(
                "Delivered order must have delivered_at"
            )

        now = self.now_provider()

        if not isinstance(now, datetime):
            raise ValueError(
                "Now provider must return a datetime"
            )

        if now < order.delivered_at:
            raise ValueError(
                "Current time cannot be before delivered_at"
            )

        return_deadline = (
            order.delivered_at
            + timedelta(days=self.return_window_days)
        )

        if now > return_deadline:
            raise ValueError(
                "Return window has expired"
            )

    def is_within_window(self, order: Order) -> bool:
        try:
            self.validate(order)
        except ValueError:
            return False

        return True