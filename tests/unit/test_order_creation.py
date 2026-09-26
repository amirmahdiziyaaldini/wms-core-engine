from datetime import date
from decimal import Decimal

import pytest

from app.domain.enums.warehouse_type import WarehouseType
from app.domain.models.base_product import BaseProduct
from app.domain.models.batch import Batch
from app.domain.models.inventory import Inventory
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.domain.models.sales_rule_context import SalesRuleContext
from app.domain.models.warehouse import Warehouse
from app.strategies.sales_rules.sales_rule import SalesRule
from app.services.order_service import OrderService


def create_product(
    sku: str = "SKU-001",
    price: str = "100",
) -> BaseProduct:
    return BaseProduct(
        sku=sku,
        name=f"Product {sku}",
        barcode=f"BAR-{sku}",
        category="General",
        base_price=Decimal(price),
    )


def create_inventory(
    sku: str = "SKU-001",
    quantity: int = 10,
) -> Inventory:
    warehouse = Warehouse(
        warehouse_id="WH-001",
        name="Main Warehouse",
        location="Frankfurt",
        warehouse_type=WarehouseType.CENTRAL,
    )

    inventory = Inventory(
        warehouse=warehouse,
    )

    batch = Batch(
        batch_id=f"BATCH-{sku}",
        product=create_product(sku),
        quantity=quantity,
        entry_date=date.today(),
    )

    inventory.add_batch(batch)

    return inventory


def create_order(
    sku: str = "SKU-001",
    quantity: int = 2,
) -> Order:
    order = Order(
        order_id="ORD-001",
        customer_id="CUS-001",
    )

    order.add_item(
        OrderItem(
            item_id="ITEM-001",
            sku=sku,
            quantity=quantity,
        )
    )

    return order


def test_create_order_resolves_product_and_saves_order():
    service = OrderService()

    product = create_product()

    service.product_repository.save(product)

    inventory = create_inventory()

    order = create_order()

    reservations = service.create_order(
        order=order,
        inventory=inventory,
    )

    assert len(reservations) == 1
    assert service.order_repository.exists("ORD-001")
    assert service.order_repository.get("ORD-001") is order


def test_create_order_prices_order_before_saving():
    service = OrderService()

    product = create_product(
        price="100",
    )

    service.product_repository.save(product)

    inventory = create_inventory()

    order = create_order(
        quantity=6,
    )

    service.create_order(
        order=order,
        inventory=inventory,
    )

    item = order.items[0]

    assert item.unit_price == Decimal("90")
    assert item.line_total == Decimal("540")
    assert order.total_amount == Decimal("540")


def test_create_order_reduces_available_stock():
    service = OrderService()

    service.product_repository.save(
        create_product()
    )

    inventory = create_inventory(
        quantity=10,
    )

    order = create_order(
        quantity=4,
    )

    service.create_order(
        order=order,
        inventory=inventory,
    )

    assert inventory.get_physical_stock(
        "SKU-001"
    ) == 10

    assert inventory.get_reserved_stock(
        "SKU-001"
    ) == 4

    assert inventory.get_available_stock(
        "SKU-001"
    ) == 6


def test_create_order_rejects_unknown_sku_before_reservation():
    service = OrderService()

    inventory = create_inventory(
        quantity=10,
    )

    order = create_order(
        sku="UNKNOWN",
        quantity=2,
    )

    with pytest.raises(ValueError):
        service.create_order(
            order=order,
            inventory=inventory,
        )

    assert inventory.get_reserved_stock(
        "SKU-001"
    ) == 0

    assert not service.order_repository.exists(
        "ORD-001"
    )


def test_create_order_does_not_save_when_stock_is_insufficient():
    service = OrderService()

    service.product_repository.save(
        create_product()
    )

    inventory = create_inventory(
        quantity=3,
    )

    order = create_order(
        quantity=5,
    )

    with pytest.raises(ValueError):
        service.create_order(
            order=order,
            inventory=inventory,
        )

    assert inventory.get_reserved_stock(
        "SKU-001"
    ) == 0

    assert inventory.get_available_stock(
        "SKU-001"
    ) == 3

    assert not service.order_repository.exists(
        "ORD-001"
    )


def test_create_order_multiple_items_is_atomic():
    service = OrderService()

    product_one = create_product(
        sku="SKU-001",
        price="100",
    )

    product_two = create_product(
        sku="SKU-002",
        price="200",
    )

    service.product_repository.save(
        product_one
    )

    service.product_repository.save(
        product_two
    )

    warehouse = Warehouse(
        warehouse_id="WH-001",
        name="Main Warehouse",
        location="Frankfurt",
        warehouse_type=WarehouseType.CENTRAL,
    )

    inventory = Inventory(
        warehouse=warehouse,
    )

    inventory.add_batch(
        Batch(
            batch_id="BATCH-001",
            product=product_one,
            quantity=10,
            entry_date=date.today(),
        )
    )

    inventory.add_batch(
        Batch(
            batch_id="BATCH-002",
            product=product_two,
            quantity=2,
            entry_date=date.today(),
        )
    )

    order = Order(
        order_id="ORD-001",
        customer_id="CUS-001",
    )

    order.add_item(
        OrderItem(
            item_id="ITEM-001",
            sku="SKU-001",
            quantity=5,
        )
    )

    order.add_item(
        OrderItem(
            item_id="ITEM-002",
            sku="SKU-002",
            quantity=5,
        )
    )

    with pytest.raises(ValueError):
        service.create_order(
            order=order,
            inventory=inventory,
        )

    assert inventory.get_reserved_stock(
        "SKU-001"
    ) == 0

    assert inventory.get_reserved_stock(
        "SKU-002"
    ) == 0

    assert not service.order_repository.exists(
        "ORD-001"
    )


def test_create_order_rule_failure_does_not_reserve_stock():
    service = OrderService()

    product = create_product()

    service.product_repository.save(
        product
    )

    inventory = create_inventory(
        quantity=10,
    )

    order = create_order(
        quantity=2,
    )

    class FailingRule(SalesRule):

        def validate(
            self,
            context: SalesRuleContext,
        ) -> None:
            raise ValueError(
                "Rule validation failed"
            )

    service.sales_rule_engine.add_rule(
        FailingRule()
    )

    with pytest.raises(ValueError):
        service.create_order(
            order=order,
            inventory=inventory,
        )

    assert inventory.get_reserved_stock(
        "SKU-001"
    ) == 0

    assert not service.order_repository.exists(
        "ORD-001"
    )


def test_create_order_rejects_duplicate_order():
    service = OrderService()

    service.product_repository.save(
        create_product()
    )

    inventory = create_inventory()

    first_order = create_order()

    service.create_order(
        order=first_order,
        inventory=inventory,
    )

    second_order = create_order()

    with pytest.raises(ValueError):
        service.create_order(
            order=second_order,
            inventory=inventory,
        )

    assert len(
        service.order_repository.list_all()
    ) == 1