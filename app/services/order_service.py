from datetime import date, datetime

from app.domain.enums.order_status import OrderStatus
from app.domain.models.inventory import Inventory
from app.domain.models.inventory_ledger import InventoryLedger
from app.domain.models.order import Order
from app.domain.models.reservation import Reservation
from app.domain.models.sales_rule_context import SalesRuleContext
from app.domain.states.order_state_machine import OrderStateMachine
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.services.inventory_service import InventoryService
from app.services.pricing_service import PricingService
from app.services.sales_rule_engine import SalesRuleEngine


class OrderService:

    def __init__(
        self,
        inventory_service: InventoryService | None = None,
        sales_rule_engine: SalesRuleEngine | None = None,
        pricing_service: PricingService | None = None,
        order_state_machine: OrderStateMachine | None = None,
        order_repository: OrderRepository | None = None,
        product_repository: ProductRepository | None = None,
    ):
        if inventory_service is not None and not isinstance(
            inventory_service,
            InventoryService,
        ):
            raise ValueError(
                "Inventory service must be an InventoryService"
            )

        if sales_rule_engine is not None and not isinstance(
            sales_rule_engine,
            SalesRuleEngine,
        ):
            raise ValueError(
                "Sales rule engine must be a SalesRuleEngine"
            )

        if pricing_service is not None and not isinstance(
            pricing_service,
            PricingService,
        ):
            raise ValueError(
                "Pricing service must be a PricingService"
            )

        if order_state_machine is not None and not isinstance(
            order_state_machine,
            OrderStateMachine,
        ):
            raise ValueError(
                "Order state machine must be an OrderStateMachine"
            )

        if order_repository is not None and not isinstance(
            order_repository,
            OrderRepository,
        ):
            raise ValueError(
                "Order repository must be an OrderRepository"
            )

        if product_repository is not None and not isinstance(
            product_repository,
            ProductRepository,
        ):
            raise ValueError(
                "Product repository must be a ProductRepository"
            )

        if inventory_service is None:
            inventory_service = InventoryService(
                InventoryLedger()
            )

        if sales_rule_engine is None:
            sales_rule_engine = SalesRuleEngine()

        if pricing_service is None:
            pricing_service = PricingService()

        if order_state_machine is None:
            order_state_machine = OrderStateMachine()

        if order_repository is None:
            order_repository = OrderRepository()

        if product_repository is None:
            product_repository = ProductRepository()

        self.inventory_service = inventory_service
        self.sales_rule_engine = sales_rule_engine
        self.pricing_service = pricing_service
        self.order_state_machine = order_state_machine
        self.order_repository = order_repository
        self.product_repository = product_repository

    def create_order(
        self,
        order: Order,
        inventory: Inventory,
        reference_date: date | None = None,
        catalog=None,
        customer=None,
    ) -> list[Reservation]:
        if not isinstance(order, Order):
            raise ValueError(
                "Order must be an Order"
            )

        if not isinstance(inventory, Inventory):
            raise ValueError(
                "Inventory must be an Inventory"
            )

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

        if self.order_repository.exists(
            order.order_id
        ):
            raise ValueError(
                f"Order already exists: {order.order_id}"
            )

        if catalog is None:
            catalog = {}

            for item in order.items:
                product = self.product_repository.get(
                    item.sku
                )

                if product is None:
                    raise ValueError(
                        f"Product not found for SKU {item.sku}"
                    )

                catalog[item.sku] = product

        for item in order.items:
            if item.sku not in catalog:
                raise ValueError(
                    f"Product not found for SKU {item.sku}"
                )

        rule_context = SalesRuleContext(
            order=order,
            catalog=catalog,
            customer=customer,
        )

        self.sales_rule_engine.validate(
            rule_context
        )

        self.pricing_service.price_order(
            order=order,
            products_by_sku=catalog,
        )

        reservations = []

        try:
            reservations = self.reserve_order(
                order=order,
                inventory=inventory,
                reference_date=reference_date,
                catalog=catalog,
                customer=customer,
            )

            self.order_repository.save(
                order
            )

        except Exception:
            for reservation in reservations:
                if reservation.reservation_id in (
                    inventory.reservations
                ):
                    inventory.release_reservation(
                        reservation.reservation_id
                    )

            raise

        return reservations

    def reserve_order(
        self,
        order: Order,
        inventory: Inventory,
        reference_date: date | None = None,
        catalog=None,
        customer=None,
    ) -> list[Reservation]:
        if not isinstance(order, Order):
            raise ValueError(
                "Order must be an Order"
            )

        if not isinstance(inventory, Inventory):
            raise ValueError(
                "Inventory must be an Inventory"
            )

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

        rule_context = SalesRuleContext(
            order=order,
            catalog=catalog,
            customer=customer,
        )

        self.sales_rule_engine.validate(
            rule_context
        )

        if catalog is not None:
            self.pricing_service.price_order(
                order=order,
                products_by_sku=catalog,
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

            reservations.append(
                reservation
            )

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

        self.order_state_machine.transition(
            order,
            OrderStatus.RESERVED,
        )

        return reservations

    def release_order_reservations(
        self,
        order: Order,
        inventory: Inventory,
    ) -> None:
        if not isinstance(order, Order):
            raise ValueError(
                "Order must be an Order"
            )

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

    def ship_order(
        self,
        order: Order,
        inventory: Inventory,
        timestamp: datetime,
    ) -> list[str]:
        if not isinstance(order, Order):
            raise ValueError(
                "Order must be an Order"
            )

        if not isinstance(inventory, Inventory):
            raise ValueError(
                "Inventory must be an Inventory"
            )

        if not isinstance(timestamp, datetime):
            raise ValueError(
                "Timestamp must be a datetime"
            )

        if order.status != OrderStatus.PAID:
            raise ValueError(
                "Only paid orders can be shipped"
            )

        order_reservations = []

        for reservation in inventory.reservations.values():
            if reservation.order_id == order.order_id:
                order_reservations.append(
                    reservation
                )

        if not order_reservations:
            raise ValueError(
                "Order has no active reservations"
            )

        shipped_serial_numbers = []

        for reservation in order_reservations:
            serial_numbers = (
                self.inventory_service.consume_reservation(
                    inventory=inventory,
                    reservation_id=reservation.reservation_id,
                    timestamp=timestamp,
                )
            )

            shipped_serial_numbers.extend(
                serial_numbers
            )

        self.order_state_machine.transition(
            order,
            OrderStatus.SHIPPED,
        )

        return shipped_serial_numbers