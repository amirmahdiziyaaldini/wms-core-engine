from app.domain.models.order import Order


class OrderRepository:

    def __init__(self):
        self._orders: dict[str, Order] = {}

    def save(self, order: Order) -> None:
        if not isinstance(order, Order):
            raise ValueError(
                "Order must be an Order"
            )

        if order.order_id in self._orders:
            raise ValueError(
                f"Order already exists: {order.order_id}"
            )

        self._orders[order.order_id] = order

    def get(self, order_id: str) -> Order | None:
        if not isinstance(order_id, str):
            raise ValueError(
                "Order ID must be a string"
            )

        return self._orders.get(order_id)

    def list_all(self) -> list[Order]:
        return list(self._orders.values())

    def delete(self, order_id: str) -> None:
        if not isinstance(order_id, str):
            raise ValueError(
                "Order ID must be a string"
            )

        self._orders.pop(order_id, None)

    def exists(self, order_id: str) -> bool:
        if not isinstance(order_id, str):
            raise ValueError(
                "Order ID must be a string"
            )

        return order_id in self._orders