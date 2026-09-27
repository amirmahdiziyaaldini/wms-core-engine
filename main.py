from datetime import date
from decimal import Decimal

from app.domain.enums.warehouse_type import WarehouseType
from app.domain.models.base_product import BaseProduct
from app.domain.models.batch import Batch
from app.domain.models.inventory import Inventory
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.domain.models.warehouse import Warehouse
from app.services.order_service import OrderService


def main() -> None:
    warehouse = Warehouse(
        warehouse_id="WH-001",
        name="Main Warehouse",
        location="Tehran",
        warehouse_type=WarehouseType.CENTRAL,
    )

    product = BaseProduct(
        sku="LAPTOP-01",
        name="Laptop",
        barcode="123456789",
        category="Electronics",
        base_price=Decimal("500000"),
    )

    inventory = Inventory(warehouse)

    inventory.add_batch(
        Batch(
            batch_id="BATCH-001",
            product=product,
            quantity=10,
            entry_date=date(2026, 9, 1),
        )
    )

    order = Order(
        order_id="ORD-001"
    )

    order.add_item(
        OrderItem(
            item_id="ITEM-001",
            sku="LAPTOP-01",
            quantity=2,
        )
    )

    order_service = OrderService()

    reservations = order_service.reserve_order(
        order=order,
        inventory=inventory,
    )

    print(f"Order: {order.order_id}")
    print(f"Status: {order.status.value}")
    print(f"Reservations: {len(reservations)}")
    print(
        f"Available stock: "
        f"{inventory.get_available_stock(product.sku)}"
    )


if __name__ == "__main__":
    main()