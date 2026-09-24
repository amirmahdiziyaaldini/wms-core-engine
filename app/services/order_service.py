from datetime import date

from app.domain.enums.order_status import OrderStatus
from app.domain.models.inventory import Inventory
from app.domain.models.inventory_ledger import InventoryLedger
from app.domain.models.order import Order
from app.domain.models.reservation import Reservation
from app.services.inventory_service import InventoryService


class OrderService:
    def __init__(
        self,
        inventory_service: InventoryService | None = None,
    ):
        if inventory_service is not None and not isinstance(
            inventory_service,
            InventoryService,
        ):
            raise ValueError(
                "Inventory service must be an InventoryService"
            )

        if inventory_service is None:
            inventory_service = InventoryService(
                InventoryLedger()
            )

        self.inventory_service = inventory_service

    def reserve_order(
        self,
        order: Order,
        inventory: Inventory,
        reference_date: date | None = None,
    ) -> list[Reservation]:
        if not isinstance(order, Order):
            raise ValueError("Order must be an Order")

        if not isinstance(inventory, Inventory):
            raise ValueError("Inventory must be an Inventory")

        if not order.items:
            raise ValueError(
                "Order must contain at least one item"
            )

        if reference_date is not None and not isinstance(
            reference_date,
            date,
        ):
            raise ValueError(
                "Reference date must be a date"
            )

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

            batch_allocations = (
                self.inventory_service.allocate_stock(
                    inventory=inventory,
                    sku=item.sku,
                    quantity=item.quantity,
                    reference_date=reference_date,
                )
            )

            reservation = Reservation(
                reservation_id=reservation_id,
                order_id=order.order_id,
                order_item_id=item.item_id,
                sku=item.sku,
                quantity=item.quantity,
                batch_allocations=batch_allocations,
            )

            reservations.append(reservation)

        committed_reservations = []

        try:
            for reservation in reservations:
                inventory.reserve_reservation(
                    reservation
                )

                committed_reservations.append(
                    reservation
                )

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
    ) -> None:
        if not isinstance(order, Order):
            raise ValueError("Order must be an Order")

        if not isinstance(inventory, Inventory):
            raise ValueError(
                "Inventory must be an Inventory"
            )

        reservation_ids = []

        for reservation_id, reservation in (
            inventory.reservations.items()
        ):
            if reservation.order_id == order.order_id:
                reservation_ids.append(
                    reservation_id
                )

        for reservation_id in reservation_ids:
            inventory.release_reservation(
                reservation_id
            )