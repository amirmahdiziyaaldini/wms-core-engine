from datetime import datetime
from decimal import Decimal

from app.domain.enums.order_status import OrderStatus
from app.domain.models.order_item import OrderItem


class Order:

    def __init__(
        self,
        order_id: str,
        status: OrderStatus = OrderStatus.CREATED,
        customer_id: str | None = None,
        created_at: datetime | None = None,
    ):
        if not isinstance(order_id, str):
            raise ValueError(
                "Order ID must be a string"
            )

        if not order_id.strip():
            raise ValueError(
                "Order ID cannot be empty"
            )

        if not isinstance(status, OrderStatus):
            raise ValueError(
                "Status must be an OrderStatus"
            )

        if customer_id is not None:
            if not isinstance(customer_id, str):
                raise ValueError(
                    "Customer ID must be a string"
                )

            if not customer_id.strip():
                raise ValueError(
                    "Customer ID cannot be empty"
                )

        if created_at is not None:
            if not isinstance(created_at, datetime):
                raise ValueError(
                    "Created at must be a datetime"
                )

        self.order_id = order_id
        self.customer_id = customer_id
        self.status = status
        self.created_at = (
            created_at
            if created_at is not None
            else datetime.now()
        )

        self.reserved_at: datetime | None = None
        self.paid_at: datetime | None = None
        self.shipped_at: datetime | None = None
        self.completed_at: datetime | None = None

        self.items: list[OrderItem] = []

    @property
    def total_amount(self) -> Decimal | None:
        if not self.items:
            return None

        line_totals = []

        for item in self.items:
            if item.line_total is None:
                return None

            line_totals.append(
                item.line_total
            )

        return sum(
            line_totals,
            Decimal("0"),
        )

    @property
    def total(self) -> Decimal | None:
        return self.total_amount

    def add_item(
        self,
        item: OrderItem,
    ) -> None:
        if not isinstance(item, OrderItem):
            raise ValueError(
                "Item must be an OrderItem"
            )

        for existing_item in self.items:
            if existing_item.item_id == item.item_id:
                raise ValueError(
                    "Order item ID must be unique"
                )

        self.items.append(item)

    def calculate_total(self) -> Decimal:
        total = self.total_amount

        if total is None:
            raise ValueError(
                "Order total cannot be calculated before all items are priced"
            )

        return total

    def get_total(self) -> Decimal:
        return self.calculate_total()