import json
from datetime import date, datetime
from decimal import Decimal

import pytest

from app.domain.enums.order_status import OrderStatus
from app.domain.enums.warehouse_type import WarehouseType
from app.domain.models.base_product import BaseProduct
from app.domain.models.batch import Batch
from app.domain.models.inventory import Inventory
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.domain.models.warehouse import Warehouse
from app.serialization.snapshot import (
    SNAPSHOT_VERSION,
    build_snapshot,
    load_snapshot,
    save_snapshot,
)


def create_state():
    product = BaseProduct(
        sku="BOOK-001",
        name="Python Fundamentals",
        barcode="123456789",
        category="Books",
        base_price=Decimal("500000"),
    )

    warehouse = Warehouse(
        warehouse_id="WH-001",
        name="Central",
        location="Berlin",
        warehouse_type=WarehouseType.CENTRAL,
    )

    inventory = Inventory(
        warehouse
    )

    inventory.add_batch(
        Batch(
            batch_id="BATCH-001",
            product=product,
            quantity=10,
            entry_date=date(
                2026,
                9,
                26,
            ),
            unit_cost=Decimal("300000"),
        )
    )

    order = Order(
        order_id="ORD-001",
        status=OrderStatus.PAID,
        customer_id="CUS-001",
        created_at=datetime(
            2026,
            9,
            26,
            10,
            0,
            0,
        ),
    )

    order.add_item(
        OrderItem(
            item_id="ITEM-001",
            sku="BOOK-001",
            quantity=2,
            product_name="Python Fundamentals",
            unit_price=Decimal("500000"),
        )
    )

    return {
        "products": [
            product
        ],
        "warehouses": [
            warehouse
        ],
        "inventories": [
            inventory
        ],
        "orders": [
            order
        ],
    }


def test_build_snapshot_has_version_and_sections():
    snapshot = build_snapshot(
        create_state()
    )

    assert snapshot["version"] == SNAPSHOT_VERSION

    assert len(
        snapshot["products"]
    ) == 1

    assert len(
        snapshot["warehouses"]
    ) == 1

    assert len(
        snapshot["inventories"]
    ) == 1

    assert len(
        snapshot["orders"]
    ) == 1


def test_save_snapshot_creates_valid_json_file(
    tmp_path,
):
    path = (
        tmp_path
        / "system_snapshot.json"
    )

    save_snapshot(
        path,
        create_state(),
    )

    assert path.exists()

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        data["version"]
        == SNAPSHOT_VERSION
    )

    assert (
        data["products"][0]["sku"]
        == "BOOK-001"
    )


def test_load_snapshot_rebuilds_real_objects(
    tmp_path,
):
    path = (
        tmp_path
        / "system_snapshot.json"
    )

    save_snapshot(
        path,
        create_state(),
    )

    state = load_snapshot(
        path
    )

    product = state["products"][0]
    warehouse = state["warehouses"][0]
    inventory = state["inventories"][0]
    order = state["orders"][0]

    assert isinstance(
        product,
        BaseProduct,
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

    assert (
        inventory.warehouse
        is warehouse
    )

    assert (
        inventory.batches[0].product
        is product
    )

    assert (
        inventory.batches[0].quantity
        == 10
    )

    assert (
        order.items[0].sku
        == "BOOK-001"
    )

    assert (
        order.items[0].unit_price
        == Decimal("500000")
    )

    assert (
        order.status
        == OrderStatus.PAID
    )


def test_load_snapshot_missing_file_has_clear_error(
    tmp_path,
):
    with pytest.raises(
        FileNotFoundError,
        match="Snapshot file not found",
    ):
        load_snapshot(
            tmp_path
            / "missing.json"
        )


def test_load_snapshot_rejects_wrong_version(
    tmp_path,
):
    path = (
        tmp_path
        / "wrong_version.json"
    )

    data = build_snapshot(
        create_state()
    )

    data["version"] = 999

    path.write_text(
        json.dumps(data),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported snapshot version",
    ):
        load_snapshot(
            path
        )