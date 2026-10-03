from datetime import date, datetime
from decimal import Decimal

from app.domain.enums.order_status import OrderStatus
from app.domain.enums.return_reason import ReturnReason
from app.domain.enums.warehouse_type import WarehouseType
from app.domain.models.base_product import BaseProduct
from app.domain.models.batch import Batch
from app.domain.models.bundle_component import BundleComponent
from app.domain.models.bundle_product import BundleProduct
from app.domain.models.inventory import Inventory
from app.domain.models.order import Order, OrderItem
from app.domain.models.return_item import ReturnItem
from app.domain.models.return_request import ReturnRequest
from app.domain.models.variant_product import VariantProduct
from app.domain.models.warehouse import Warehouse
from app.repositories.in_memory_repository import InMemoryRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.serialization.snapshot import load_snapshot, save_snapshot


def create_snapshot_state():
    parent_product = BaseProduct(
        sku="PHONE-001",
        name="Phone",
        barcode="PHONE001",
        category="Electronics",
        base_price=Decimal("500000"),
    )

    variant_product = VariantProduct(
        sku="PHONE-001-BLACK",
        name="Phone Black",
        barcode="PHONEBLACK001",
        category="Electronics",
        attributes={
            "color": "black",
        },
        price_modifier=Decimal("50000"),
        parent_product=parent_product,
    )

    bundle_product = BundleProduct(
        sku="PHONE-BUNDLE-001",
        name="Phone Bundle",
        barcode="PHONEBUNDLE001",
        category="Electronics",
        base_price=Decimal("1000000"),
        components=[
            BundleComponent(
                product=parent_product,
                required_quantity=1,
            ),
            BundleComponent(
                product=variant_product,
                required_quantity=1,
            ),
        ],
    )

    warehouse_one = Warehouse(
        warehouse_id="WH-001",
        name="Main Warehouse",
        location="Tehran",
        warehouse_type=WarehouseType.CENTRAL,
    )

    warehouse_two = Warehouse(
        warehouse_id="WH-002",
        name="Backup Warehouse",
        location="Karaj",
        warehouse_type=WarehouseType.CENTRAL,
    )

    inventory_one = Inventory(
        warehouse=warehouse_one,
    )

    inventory_two = Inventory(
        warehouse=warehouse_two,
    )

    batch_one = Batch(
        batch_id="BATCH-001",
        product=variant_product,
        quantity=10,
        entry_date=date(2026, 9, 1),
        unit_cost=Decimal("450000"),
    )

    batch_two = Batch(
        batch_id="BATCH-002",
        product=variant_product,
        quantity=5,
        entry_date=date(2026, 9, 2),
        unit_cost=Decimal("460000"),
    )

    inventory_one.add_batch(batch_one)
    inventory_two.add_batch(batch_two)

    order = Order(
        order_id="ORD-001",
        status=OrderStatus.PAID,
        created_at=datetime(
            2026,
            9,
            10,
            9,
            0,
            0,
        ),
    )

    order.add_item(
        OrderItem(
            item_id="ITEM-001",
            sku="PHONE-001-BLACK",
            quantity=2,
            unit_price=Decimal("550000"),
        )
    )

    order.paid_at = datetime(
        2026,
        9,
        10,
        10,
        0,
        0,
    )

    return_item = ReturnItem(
        sku="PHONE-001-BLACK",
        quantity=1,
    )

    return_request = ReturnRequest(
        return_id="RET-001",
        order=order,
        reason=ReturnReason.CUSTOMER_CHANGED_MIND,
        items=[
            return_item,
        ],
        requested_at=datetime(
            2026,
            9,
            11,
            10,
            0,
            0,
        ),
    )

    state = {
        "products": [
            parent_product,
            variant_product,
            bundle_product,
        ],
        "warehouses": [
            warehouse_one,
            warehouse_two,
        ],
        "inventories": [
            inventory_one,
            inventory_two,
        ],
        "orders": [
            order,
        ],
        "returns": [
            return_request,
        ],
        "transfers": [],
        "inventory_logs": [],
        "return_receipts": [],
        "serialized_units": [],
        "shipments": [],
        "payment_transactions": [],
        "financial_logs": [],
    }

    return state


def test_snapshot_round_trip_preserves_object_graph_and_repository_usability(
    tmp_path,
):
    path = tmp_path / "system_snapshot.json"

    original_state = create_snapshot_state()

    save_snapshot(
        path,
        original_state,
    )

    loaded_state = load_snapshot(
        path,
    )

    parent_product = loaded_state["products"][0]
    variant_product = loaded_state["products"][1]
    bundle_product = loaded_state["products"][2]

    warehouse_one = loaded_state["warehouses"][0]
    warehouse_two = loaded_state["warehouses"][1]

    inventory_one = loaded_state["inventories"][0]
    inventory_two = loaded_state["inventories"][1]

    order = loaded_state["orders"][0]
    return_request = loaded_state["returns"][0]

    assert isinstance(
        variant_product,
        VariantProduct,
    )

    assert isinstance(
        bundle_product,
        BundleProduct,
    )

    assert isinstance(
        warehouse_one,
        Warehouse,
    )

    assert isinstance(
        warehouse_two,
        Warehouse,
    )

    assert isinstance(
        inventory_one,
        Inventory,
    )

    assert isinstance(
        inventory_two,
        Inventory,
    )

    assert isinstance(
        order,
        Order,
    )

    assert isinstance(
        return_request,
        ReturnRequest,
    )

    assert (
        variant_product.parent_product
        is parent_product
    )

    assert (
        bundle_product.components[0].product
        is parent_product
    )

    assert (
        bundle_product.components[1].product
        is variant_product
    )

    assert (
        inventory_one.warehouse
        is warehouse_one
    )

    assert (
        inventory_two.warehouse
        is warehouse_two
    )

    assert (
        inventory_one.batches[0].product
        is variant_product
    )

    assert (
        inventory_two.batches[0].product
        is variant_product
    )

    assert (
        inventory_one.batches[0].quantity
        == 10
    )

    assert (
        inventory_two.batches[0].quantity
        == 5
    )

    assert (
        inventory_one.get_physical_stock(
            "PHONE-001-BLACK"
        )
        == 10
    )

    assert (
        inventory_two.get_physical_stock(
            "PHONE-001-BLACK"
        )
        == 5
    )

    assert (
        order.items[0].item_id
        == "ITEM-001"
    )

    assert (
        order.items[0].sku
        == "PHONE-001-BLACK"
    )

    assert (
        order.items[0].unit_price
        == Decimal("550000")
    )

    assert (
        return_request.order_id
        == order.order_id
    )

    assert (
        return_request.items[0].sku
        == "PHONE-001-BLACK"
    )

    assert (
        return_request.items[0].quantity
        == 1
    )

    product_repository = ProductRepository()
    order_repository = OrderRepository()

    warehouse_repository = InMemoryRepository()
    return_repository = InMemoryRepository()

    for product in loaded_state["products"]:
        product_repository.save(product)

    for loaded_order in loaded_state["orders"]:
        order_repository.save(loaded_order)

    for warehouse in loaded_state["warehouses"]:
        warehouse_repository.save(
            warehouse.warehouse_id,
            warehouse,
        )

    for loaded_return in loaded_state["returns"]:
        return_repository.save(
            loaded_return.return_id,
            loaded_return,
        )

    restored_variant = product_repository.get(
        "PHONE-001-BLACK"
    )

    restored_bundle = product_repository.get(
        "PHONE-BUNDLE-001"
    )

    restored_order = order_repository.get(
        "ORD-001"
    )

    restored_warehouse = warehouse_repository.get(
        "WH-002"
    )

    restored_return = return_repository.get(
        "RET-001"
    )

    assert restored_variant is variant_product
    assert restored_bundle is bundle_product
    assert restored_order is order
    assert restored_warehouse is warehouse_two
    assert restored_return is return_request

    assert (
        restored_variant.parent_product
        is parent_product
    )

    assert (
        restored_bundle.components[1].product
        is restored_variant
    )

    assert (
        restored_return.order_id
        == restored_order.order_id
    )

    assert (
        inventory_two.get_available_stock(
            "PHONE-001-BLACK"
        )
        == 5
    )


def test_snapshot_round_trip_keeps_json_persistence_boundary(
    tmp_path,
):
    path = tmp_path / "system_snapshot.json"

    original_state = create_snapshot_state()

    save_snapshot(
        path,
        original_state,
    )

    loaded_state = load_snapshot(
        path,
    )

    assert path.exists()

    assert len(
        loaded_state["products"]
    ) == 3

    assert len(
        loaded_state["warehouses"]
    ) == 2

    assert len(
        loaded_state["inventories"]
    ) == 2

    assert len(
        loaded_state["orders"]
    ) == 1

    assert len(
        loaded_state["returns"]
    ) == 1

    assert len(
        loaded_state["transfers"]
    ) == 0

    assert len(
        loaded_state["financial_logs"]
    ) == 0