from typing import Any

from app.domain.models.order import Order


class SalesRuleContext:
    def __init__(
        self,
        order: Order,
        catalog: Any = None,
        customer: Any = None,
    ):
        if not isinstance(order, Order):
            raise ValueError("Order must be an Order")

        self.order = order
        self.catalog = catalog
        self.customer = customer