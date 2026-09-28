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

    warehouse = Warehouse(
        warehouse_id="WH-001",
        name="Main Warehouse",
        location="Tehran",
        warehouse_type=WarehouseType.CENTRAL,
    )

    inventory = Inventory(
        warehouse=warehouse,
    )

    batch = Batch(
        batch_id="BATCH-001",
        product=variant_product,
        quantity=10,
        entry_date=date(2026, 9, 1),
        unit_cost=Decimal("450000"),
    )

    inventory.add_batch(batch)

    order = Order(
        order_id="ORD-001",
        status=OrderStatus.PAID,
        created_at=datetime(2026, 9, 10, 9, 0, 0),
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
        items=[return_item],
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
            warehouse,
        ],
        "inventories": [
            inventory,
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


def test_snapshot_round_trip_preserves_object_graph(
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

    warehouse = loaded_state["warehouses"][0]
    inventory = loaded_state["inventories"][0]
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
        warehouse,
        Warehouse,
    )

    assert isinstance(
        inventory,
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
        inventory.warehouse
        is warehouse
    )

    assert (
        inventory.batches[0].product
        is variant_product
    )

    assert (
        inventory.batches[0].quantity
        == 10
    )

    assert (
        inventory.get_physical_stock(
            "PHONE-001-BLACK"
        )
        == 10
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
        order.status
        == OrderStatus.PAID
    )

    assert (
        order.paid_at
        == datetime(
            2026,
            9,
            10,
            10,
            0,
            0,
        )
    )


    assert (
        return_request.items[0].sku
        == "PHONE-001-BLACK"
    )

    assert (
        return_request.items[0].quantity
        == 1
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

    assert len(
        loaded_state["products"]
    ) == 3

    assert len(
        loaded_state["warehouses"]
    ) == 1

    assert len(
        loaded_state["inventories"]
    ) == 1

    assert len(
        loaded_state["orders"]
    ) == 1

    assert len(
        loaded_state["returns"]
    ) == 1

    assert path.exists()