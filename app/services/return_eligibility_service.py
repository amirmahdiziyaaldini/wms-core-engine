from app.domain.enums.order_status import OrderStatus
from app.domain.models.order import Order


class ReturnEligibilityService:

    def validate_order_eligibility(self, order: Order) -> None:
        if not isinstance(order, Order):
            raise ValueError("Order must be an Order")

        if order.status == OrderStatus.DELIVERED:
            return

        if order.status == OrderStatus.PAID:
            raise ValueError(
                "Paid orders that have not been delivered must use "
                "cancellation or refund instead of RMA"
            )

        if order.status == OrderStatus.CREATED:
            raise ValueError(
                "Created orders are not eligible for RMA"
            )

        if order.status == OrderStatus.RESERVED:
            raise ValueError(
                "Reserved orders are not eligible for RMA"
            )

        if order.status == OrderStatus.SHIPPED:
            raise ValueError(
                "Shipped orders are not eligible for RMA until delivery"
            )

        if order.status == OrderStatus.CANCELLED:
            raise ValueError(
                "Cancelled orders are not eligible for RMA"
            )

        raise ValueError(
            "Order is not eligible for RMA"
        )

    def is_eligible(self, order: Order) -> bool:
        if not isinstance(order, Order):
            raise ValueError("Order must be an Order")

        return order.status == OrderStatus.DELIVERED