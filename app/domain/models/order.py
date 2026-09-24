from app.domain.enums.order_status import OrderStatus
from app.domain.models.order_item import OrderItem


class Order:
    def __init__(
        self,
        order_id: str,
        status: OrderStatus = OrderStatus.CREATED,
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

        self.order_id = order_id
        self.status = status
        self.items: list[OrderItem] = []

    def add_item(self, item: OrderItem):
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