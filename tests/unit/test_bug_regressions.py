import json
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from decimal import Decimal

import pytest

from app.domain.enums.inventory_transaction_type import InventoryTransactionType
from app.domain.enums.order_status import OrderStatus
from app.domain.enums.return_reason import ReturnReason
from app.domain.enums.return_status import ReturnStatus
from app.domain.enums.warehouse_type import WarehouseType
from app.domain.models.base_product import BaseProduct
from app.domain.models.batch import Batch
from app.domain.models.inventory import Inventory
from app.domain.models.inventory_ledger import InventoryLedger
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.domain.models.reservation import Reservation
from app.domain.models.return_item import ReturnItem
from app.domain.models.return_request import ReturnRequest
from app.domain.models.warehouse import Warehouse
from app.serialization.serializer import serialize_entity
from app.serialization.snapshot import build_snapshot, load_snapshot, save_snapshot
from app.services.inventory_service import InventoryService
from app.services.order_service import OrderService
from app.services.refund_service import RefundService
from app.services.return_receiving_service import ReturnReceivingService
from app.strategies.fifo_stock_allocation_strategy import FIFOStockAllocationStrategy
from app.strategies.lifo_stock_allocation_strategy import LIFOStockAllocationStrategy


def create_product(sku="SKU-001"):
    return BaseProduct(
        sku=sku,
        name="Product",
        barcode=f"BAR-{sku}",
        category="General",
        base_price=Decimal("100"),
    )


def create_inventory(product=None, quantity=10):
    product = product or create_product()
    warehouse = Warehouse(
        warehouse_id="WH-001",
        name="Main",
        location="Frankfurt",
        warehouse_type=WarehouseType.CENTRAL,
    )
    inventory = Inventory(warehouse)
    inventory.add_batch(
        Batch(
            batch_id="BATCH-001",
            product=product,
            quantity=quantity,
            entry_date=date(2026, 9, 1),
        )
    )
    return inventory


def create_order(status=OrderStatus.CREATED, sku="SKU-001", quantity=2):
    order = Order(order_id="ORD-001", status=status)
    order.add_item(
        OrderItem(
            item_id="ITEM-001",
            sku=sku,
            quantity=quantity,
            unit_price=Decimal("100"),
        )
    )
    return order


def test_reserve_order_invalid_state_does_not_mutate_inventory():
    inventory = create_inventory()
    order = create_order(status=OrderStatus.PAID)
    service = OrderService()

    with pytest.raises(ValueError, match="Invalid order transition"):
        service.reserve_order(order, inventory)

    assert order.status == OrderStatus.PAID
    assert inventory.reservations == {}
    assert inventory.get_available_stock("SKU-001") == 10


def test_reserve_order_rolls_back_if_state_transition_fails(monkeypatch):
    inventory = create_inventory()
    order = create_order()
    service = OrderService()

    original_transition = service.order_state_machine.transition

    def failing_transition(*args, **kwargs):
        raise ValueError("Simulated transition failure")

    monkeypatch.setattr(
        service.order_state_machine,
        "transition",
        failing_transition,
    )

    with pytest.raises(ValueError, match="Simulated transition failure"):
        service.reserve_order(order, inventory)

    assert order.status == OrderStatus.CREATED
    assert inventory.reservations == {}
    assert inventory.get_available_stock("SKU-001") == 10
    monkeypatch.setattr(
        service.order_state_machine,
        "transition",
        original_transition,
    )


def test_refund_uses_discount_for_partial_return():
    order = Order(order_id="ORD-001")
    order.add_item(
        OrderItem(
            item_id="ITEM-001",
            sku="SKU-001",
            quantity=2,
            unit_price=Decimal("100"),
            discount=Decimal("20"),
        )
    )

    return_request = ReturnRequest(
        return_id="RET-001",
        order=order,
        reason=ReturnReason.CUSTOMER_CHANGED_MIND,
        items=[
            ReturnItem(
                sku="SKU-001",
                quantity=1,
                order_item_id="ITEM-001",
            )
        ],
    )
    return_request._set_status(
        ReturnStatus.APPROVED,
        datetime(2026, 9, 28, 10, 0),
    )

    refund = RefundService().refund(
        return_request=return_request,
        order=order,
        timestamp=datetime(2026, 9, 28, 11, 0),
    )

    assert refund.amount == Decimal("90")


def test_duplicate_sku_return_requires_order_item_reference():
    order = Order(order_id="ORD-001")
    order.add_item(
        OrderItem(
            item_id="ITEM-001",
            sku="SKU-001",
            quantity=1,
            unit_price=Decimal("100"),
        )
    )
    order.add_item(
        OrderItem(
            item_id="ITEM-002",
            sku="SKU-001",
            quantity=1,
            unit_price=Decimal("200"),
        )
    )

    with pytest.raises(ValueError, match="Order item reference is required"):
        ReturnRequest(
            return_id="RET-001",
            order=order,
            reason=ReturnReason.CUSTOMER_CHANGED_MIND,
            items=[ReturnItem(sku="SKU-001", quantity=1)],
        )


def test_reservation_rejects_partial_batch_allocation():
    with pytest.raises(
        ValueError,
        match="Total batch allocation must equal reservation quantity",
    ):
        Reservation(
            reservation_id="RES-001",
            order_id="ORD-001",
            order_item_id="ITEM-001",
            sku="SKU-001",
            quantity=10,
            batch_allocations={"BATCH-001": 3},
        )


def test_inventory_rejects_unknown_reservation_batch():
    inventory = create_inventory()
    reservation = Reservation(
        reservation_id="RES-001",
        order_id="ORD-001",
        order_item_id="ITEM-001",
        sku="SKU-001",
        quantity=4,
        batch_allocations={"BATCH-999": 4},
    )

    with pytest.raises(ValueError, match="Batch BATCH-999 not found in inventory"):
        inventory.reserve_reservation(reservation)


def test_serialized_batch_quantity_change_requires_matching_serials():
    from app.domain.models.serialized_product import SerializedProduct

    product = SerializedProduct(
        sku="SER-001",
        name="Serialized",
        barcode="SER001",
        category="General",
        base_price=Decimal("100"),
    )
    batch = Batch(
        batch_id="BATCH-SER",
        product=product,
        quantity=2,
        entry_date=date(2026, 9, 1),
        serial_numbers=["S1", "S2"],
    )

    with pytest.raises(ValueError, match="Number of serial numbers"):
        batch.quantity = 1

    batch.serial_numbers = ["S2"]
    batch.quantity = 1
    assert batch.quantity == 1
    assert batch.serial_numbers == ["S2"]


def test_snapshot_load_rejects_duplicate_root_identifier(tmp_path):
    product = create_product()
    snapshot = build_snapshot({"products": [product]})
    snapshot["products"].append(dict(snapshot["products"][0]))
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot), encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate snapshot identifier"):
        load_snapshot(path)


def test_snapshot_load_rejects_invalid_product_field_type(tmp_path):
    product = create_product()
    snapshot = build_snapshot({"products": [product]})
    snapshot["products"][0]["name"] = 123
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot), encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid string field 'name'"):
        load_snapshot(path)


def test_snapshot_load_rejects_reservation_unknown_batch(tmp_path):
    product = create_product()
    warehouse = Warehouse(
        warehouse_id="WH-001",
        name="Main",
        location="Frankfurt",
        warehouse_type=WarehouseType.CENTRAL,
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
    order = create_order()
    reservation = Reservation(
        reservation_id="RES-001",
        order_id=order.order_id,
        order_item_id=order.items[0].item_id,
        sku=product.sku,
        quantity=2,
        batch_allocations={"BATCH-001": 2},
    )
    inventory.reservations[reservation.reservation_id] = reservation
    reservation.batch_allocations["BATCH-999"] = 1
    reservation.batch_allocations["BATCH-001"] = 1

    snapshot = build_snapshot({
        "products": [product],
        "warehouses": [warehouse],
        "inventories": [inventory],
        "orders": [order],
    })
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot), encoding="utf-8")

    with pytest.raises(ValueError, match="unknown batch"):
        load_snapshot(path)


def test_serializer_rejects_none_entity():
    with pytest.raises(ValueError, match="Entity cannot be None"):
        serialize_entity(None)


def test_snapshot_save_is_safe_for_concurrent_writers(tmp_path):
    path = tmp_path / "snapshot.json"
    state = {"products": [create_product()]}

    def save():
        save_snapshot(path, state)

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(lambda _: save(), range(8)))

    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["products"][0]["sku"] == "SKU-001"
    assert not list(tmp_path.glob("*.tmp"))


def test_cancel_order_records_release_transaction():
    inventory = create_inventory()
    ledger = InventoryLedger()
    service = OrderService(
        inventory_service=InventoryService(ledger),
    )
    order = create_order()

    service.reserve_order(order, inventory)
    service.cancel_order(order, inventory)

    assert order.status == OrderStatus.CANCELLED
    release_transactions = [
        transaction
        for transaction in ledger.transactions
        if transaction.transaction_type == InventoryTransactionType.RELEASE_RESERVATION
    ]
    assert len(release_transactions) == 1
    assert release_transactions[0].reference_id == order.order_id
    assert release_transactions[0].quantity == -2


def test_fifo_and_lifo_ignore_expired_batches_without_reference_date():
    product = create_product()
    expired = Batch(
        batch_id="EXPIRED",
        product=product,
        quantity=5,
        entry_date=date(2026, 1, 1),
        expiry_date=date(2026, 1, 10),
    )
    valid = Batch(
        batch_id="VALID",
        product=product,
        quantity=5,
        entry_date=date(2026, 1, 2),
        expiry_date=date(2027, 1, 1),
    )

    assert FIFOStockAllocationStrategy().allocate([expired, valid], 3) == {"VALID": 3}
    assert LIFOStockAllocationStrategy().allocate([expired, valid], 3) == {"VALID": 3}


def test_return_receiving_is_cumulative():
    order = create_order(quantity=5)
    request = ReturnRequest(
        return_id="RET-001",
        order=order,
        reason=ReturnReason.CUSTOMER_CHANGED_MIND,
        items=[ReturnItem(sku="SKU-001", quantity=5)],
    )
    service = ReturnReceivingService()

    service.receive(request, "SKU-001", 3, receipt_id="R1")
    service.receive(request, "SKU-001", 2, receipt_id="R2")

    with pytest.raises(ValueError, match="cumulatively"):
        service.receive(request, "SKU-001", 1, receipt_id="R3")


def test_receive_rolls_back_batch_when_ledger_fails(monkeypatch):
    inventory = create_inventory()
    ledger = InventoryLedger()
    service = InventoryService(ledger)
    batch = Batch(
        batch_id="BATCH-NEW",
        product=inventory.batches[0].product,
        quantity=3,
        entry_date=date(2026, 9, 2),
    )

    def fail_record(transaction):
        raise RuntimeError("ledger failure")

    monkeypatch.setattr(ledger, "record", fail_record)

    with pytest.raises(RuntimeError, match="ledger failure"):
        service.receive(inventory, batch, reference_id="REC-001")

    assert [item.batch_id for item in inventory.batches] == ["BATCH-001"]
    assert ledger.transactions == []


def test_reserve_rolls_back_reservation_when_ledger_fails(monkeypatch):
    inventory = create_inventory()
    ledger = InventoryLedger()
    service = InventoryService(ledger)
    reservation = Reservation(
        reservation_id="RES-001",
        order_id="ORD-001",
        order_item_id="ITEM-001",
        sku="SKU-001",
        quantity=2,
    )

    monkeypatch.setattr(
        ledger,
        "record",
        lambda transaction: (_ for _ in ()).throw(RuntimeError("ledger failure")),
    )

    with pytest.raises(RuntimeError, match="ledger failure"):
        service.reserve_reservation(inventory, reservation)

    assert inventory.reservations == {}
    assert ledger.transactions == []


def test_release_rolls_back_reservation_when_ledger_fails(monkeypatch):
    inventory = create_inventory()
    ledger = InventoryLedger()
    service = InventoryService(ledger)
    reservation = Reservation(
        reservation_id="RES-001",
        order_id="ORD-001",
        order_item_id="ITEM-001",
        sku="SKU-001",
        quantity=2,
    )
    inventory.reserve_reservation(reservation)

    monkeypatch.setattr(
        ledger,
        "record",
        lambda transaction: (_ for _ in ()).throw(RuntimeError("ledger failure")),
    )

    with pytest.raises(RuntimeError, match="ledger failure"):
        service.release_reservation(inventory, "RES-001")

    assert inventory.reservations["RES-001"] is reservation
    assert ledger.transactions == []


def test_consume_serialized_reservation_rolls_back_atomically(monkeypatch):
    from app.domain.models.serialized_product import SerializedProduct

    product = SerializedProduct(
        sku="SER-001",
        name="Serialized",
        barcode="SER001",
        category="General",
        base_price=Decimal("100"),
    )
    warehouse = Warehouse(
        warehouse_id="WH-SER",
        name="Serialized Warehouse",
        location="Frankfurt",
        warehouse_type=WarehouseType.CENTRAL,
    )
    inventory = Inventory(warehouse)
    batch = Batch(
        batch_id="BATCH-SER",
        product=product,
        quantity=3,
        entry_date=date(2026, 9, 1),
        serial_numbers=["S1", "S2", "S3"],
    )
    inventory.add_batch(batch)
    reservation = Reservation(
        reservation_id="RES-SER",
        order_id="ORD-SER",
        order_item_id="ITEM-SER",
        sku="SER-001",
        quantity=1,
        batch_allocations={"BATCH-SER": 1},
    )
    inventory.reserve_reservation(reservation)
    ledger = InventoryLedger()
    service = InventoryService(ledger)

    monkeypatch.setattr(
        ledger,
        "record",
        lambda transaction: (_ for _ in ()).throw(RuntimeError("ledger failure")),
    )

    with pytest.raises(RuntimeError, match="ledger failure"):
        service.consume_reservation(
            inventory,
            "RES-SER",
            datetime(2026, 9, 2, 10, 0),
        )

    assert batch.quantity == 3
    assert batch.serial_numbers == ["S1", "S2", "S3"]
    assert inventory.reservations["RES-SER"] is reservation
    assert ledger.transactions == []


def test_stock_transfer_dispatch_serialized_rollback(monkeypatch):
    from app.domain.enums.transfer_status import TransferStatus
    from app.domain.models.serialized_product import SerializedProduct
    from app.domain.models.stock_transfer import StockTransferItem
    from app.services.stock_transfer_service import StockTransferService

    product = SerializedProduct(
        sku="SER-001",
        name="Serialized",
        barcode="SER001",
        category="General",
        base_price=Decimal("100"),
    )
    source_warehouse = Warehouse(
        warehouse_id="WH-SOURCE",
        name="Source",
        location="Frankfurt",
        warehouse_type=WarehouseType.CENTRAL,
    )
    destination_warehouse = Warehouse(
        warehouse_id="WH-DEST",
        name="Destination",
        location="Frankfurt",
        warehouse_type=WarehouseType.CENTRAL,
    )
    source = Inventory(source_warehouse)
    destination = Inventory(destination_warehouse)
    batch = Batch(
        batch_id="BATCH-SER",
        product=product,
        quantity=3,
        entry_date=date(2026, 9, 1),
        serial_numbers=["S1", "S2", "S3"],
    )
    source.add_batch(batch)
    ledger = InventoryLedger()
    inventory_service = InventoryService(ledger)
    transfer_service = StockTransferService(
        source,
        destination,
        inventory_service,
    )
    transfer = transfer_service.create_transfer(
        "TR-001",
        [StockTransferItem("SER-001", 1)],
        datetime(2026, 9, 2, 10, 0),
    )

    monkeypatch.setattr(
        ledger,
        "record",
        lambda transaction: (_ for _ in ()).throw(RuntimeError("ledger failure")),
    )

    with pytest.raises(RuntimeError, match="ledger failure"):
        transfer_service.dispatch(
            transfer,
            datetime(2026, 9, 2, 10, 0),
        )

    assert batch.quantity == 3
    assert batch.serial_numbers == ["S1", "S2", "S3"]
    assert transfer.status == TransferStatus.CREATED
    assert transfer.dispatched_at is None
    assert transfer.items[0].batch_allocations == {}
    assert transfer.items[0].serial_allocations == {}
    assert ledger.transactions == []


def test_snapshot_rejects_negative_base_price(tmp_path):
    product = create_product()
    snapshot = build_snapshot({"products": [product]})
    snapshot["products"][0]["base_price"] = "-10"
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot), encoding="utf-8")

    with pytest.raises(ValueError, match="Base price cannot be negative"):
        load_snapshot(path)


def test_return_receipt_round_trip():
    from app.domain.models.return_receipt import ReturnReceipt
    from app.serialization.deserializer import deserialize_entity

    receipt = ReturnReceipt(
        receipt_id="RECEIPT-001",
        return_id="RET-001",
        sku="SKU-001",
        quantity=2,
        serial_numbers=["S1", "S2"],
    )

    restored = deserialize_entity(serialize_entity(receipt))

    assert restored.receipt_id == receipt.receipt_id
    assert restored.return_id == receipt.return_id
    assert restored.serial_numbers == ["S1", "S2"]


def test_stock_transfer_item_serial_allocations_round_trip():
    from app.domain.models.stock_transfer import StockTransferItem
    from app.serialization.deserializer import deserialize_entity

    item = StockTransferItem(
        sku="SER-001",
        quantity=2,
        batch_allocations={"BATCH-001": 2},
        serial_allocations={"BATCH-001": ["S1", "S2"]},
    )

    restored = deserialize_entity(serialize_entity(item))

    assert restored.batch_allocations == {"BATCH-001": 2}
    assert restored.serial_allocations == {"BATCH-001": ["S1", "S2"]}


def test_deserialization_rejects_duplicate_payment_transaction():
    from app.domain.models.payment_transaction import PaymentTransaction
    from app.serialization.deserializer import DeserializationContext, DeserializationError, deserialize_entity

    transaction = PaymentTransaction(
        transaction_id="PAY-001",
        order_id="ORD-001",
        reference="REF-001",
        amount=Decimal("100"),
    )
    context = DeserializationContext()
    deserialize_entity(serialize_entity(transaction), context)

    with pytest.raises(DeserializationError, match="Duplicate payment transaction ID"):
        deserialize_entity(serialize_entity(transaction), context)


def test_deserialization_rejects_duplicate_financial_transaction():
    from app.domain.enums.financial_transaction_type import FinancialTransactionType
    from app.domain.models.financial_transaction import FinancialTransaction
    from app.serialization.deserializer import DeserializationContext, DeserializationError, deserialize_entity

    transaction = FinancialTransaction(
        transaction_id="FIN-001",
        return_id="RET-001",
        order_id="ORD-001",
        amount=Decimal("100"),
        transaction_type=FinancialTransactionType.REFUND,
    )
    context = DeserializationContext()
    deserialize_entity(serialize_entity(transaction), context)

    with pytest.raises(DeserializationError, match="Duplicate financial transaction ID"):
        deserialize_entity(serialize_entity(transaction), context)


def test_bundle_component_rejects_boolean_quantity():
    from app.domain.models.bundle_component import BundleComponent

    with pytest.raises(ValueError, match="Required quantity must be an integer"):
        BundleComponent(create_product(), True)

    with pytest.raises(ValueError, match="Required quantity must be an integer"):
        BundleComponent(create_product(), False)


def test_snapshot_rejects_duplicate_shipments(tmp_path):
    from app.domain.models.shipment import Shipment

    shipment = Shipment(
        shipment_id="SHP-001",
        order_id="ORD-001",
        warehouse_id="WH-001",
        shipped_at=datetime(2026, 9, 2, 10, 0),
    )
    snapshot = build_snapshot({"shipments": [shipment]})
    snapshot["shipments"].append(dict(snapshot["shipments"][0]))
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot), encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate snapshot identifier"):
        load_snapshot(path)
