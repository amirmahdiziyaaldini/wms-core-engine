from app.domain.enums.order_status import OrderStatus
from app.domain.models.inventory import Inventory
from app.domain.models.order import Order
from app.domain.models.reservation import Reservation


class OrderService:
    def reserve_order(
        self,
        order: Order,
        inventory: Inventory,
    ) -> list[Reservation]:
        if not isinstance(order, Order):
            raise ValueError("Order must be an Order")

        if not isinstance(inventory, Inventory):
            raise ValueError("Inventory must be an Inventory")

        if not order.items:
            raise ValueError("Order must contain at least one item")

        for item in order.items:
            for reservation in inventory.reservations.values():
                if (
                    reservation.order_id == order.order_id
                    and reservation.order_item_id == item.item_id
                ):
                    raise ValueError(
                        "Order item is already reserved"
                    )

        for item in order.items:
            available_stock = inventory.get_available_stock(
                item.sku
            )

            if item.quantity > available_stock:
                raise ValueError(
                    f"Insufficient available stock for SKU {item.sku}"
                )

        reservations = []

        for item in order.items:
            reservation_id = (
                f"RES-{order.order_id}-{item.item_id}"
            )

            reservation = Reservation(
                reservation_id=reservation_id,
                order_id=order.order_id,
                order_item_id=item.item_id,
                sku=item.sku,
                quantity=item.quantity,
            )

            reservations.append(reservation)

        committed_reservations = []

        try:
            for reservation in reservations:
                inventory.reserve_reservation(
                    reservation
                )
                committed_reservations.append(reservation)

        except Exception:
            for reservation in committed_reservations:
                inventory.release_reservation(
                    reservation.reservation_id
                )

            raise

        order.status = OrderStatus.RESERVED

        return reservations

    def release_order_reservations(
        self,
        order: Order,
        inventory: Inventory,
    ):
        if not isinstance(order, Order):
            raise ValueError("Order must be an Order")

        if not isinstance(inventory, Inventory):
            raise ValueError("Inventory must be an Inventory")

        reservation_ids = []

        for reservation_id, reservation in inventory.reservations.items():
            if reservation.order_id == order.order_id:
                reservation_ids.append(reservation_id)

        for reservation_id in reservation_ids:
            inventory.release_reservation(
                reservation_id
            )