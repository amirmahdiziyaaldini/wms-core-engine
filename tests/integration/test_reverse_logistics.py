from datetime import date, datetime
from decimal import Decimal

from app.domain.enums.inventory_transaction_type import InventoryTransactionType
from app.domain.enums.qc_result import QCResult
from app.domain.enums.return_reason import ReturnReason
from app.domain.enums.return_status import ReturnStatus
from app.domain.enums.warehouse_type import WarehouseType
from app.domain.models.batch import Batch
from app.domain.models.base_product import BaseProduct
from app.domain.models.inventory import Inventory
from app.domain.models.inventory_ledger import InventoryLedger
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.domain.models.return_item import ReturnItem
from app.domain.models.return_request import ReturnRequest
from app.domain.models.warehouse import Warehouse
from app.domain.states.return_state_machine import ReturnStateMachine
from app.services.inventory_service import InventoryService
from app.services.qc_service import QCService
from app.services.refund_service import RefundService
from app.services.return_receiving_service import ReturnReceivingService
from app.services.rma_service import RMAService
from app.repositories.financial_transaction_repository import (
    FinancialTransactionRepository,
)


def create_product():
    return BaseProduct(
        sku="SKU-RETURN-001",
        name="Return Test Product",
        barcode="123456789",
        category="test",
        base_price=Decimal("100.00"),
    )


def create_order():
    order = Order(
        order_id="ORDER-RETURN-001",
        customer_id="CUSTOMER-001",
    )

    order.add_item(
        OrderItem(
            item_id="ITEM-001",
            sku="SKU-RETURN-001",
            quantity=2,
            unit_price=Decimal("100.00"),
        )
    )

    return order


def create_inventories(product):
    sellable_warehouse = Warehouse(
        warehouse_id="WH-CENTRAL",
        name="Central Warehouse",
        location="Main",
        warehouse_type=WarehouseType.CENTRAL,
    )

    quarantine_warehouse = Warehouse(
        warehouse_id="WH-SCRAP",
        name="Scrap Quarantine",
        location="QC",
        warehouse_type=WarehouseType.SCRAP_QUARANTINE,
    )

    sellable_inventory = Inventory(sellable_warehouse)
    quarantine_inventory = Inventory(quarantine_warehouse)

    sellable_inventory.add_batch(
        Batch(
            batch_id="BATCH-001",
            product=product,
            quantity=2,
            entry_date=date(2026, 9, 27),
            unit_cost=Decimal("70.00"),
        )
    )

    return sellable_inventory, quarantine_inventory


def move_return_to_qc(return_request, return_receipt):
    state_machine = ReturnStateMachine()

    state_machine.transition(
        return_request,
        ReturnStatus.QC_INSPECTION,
        return_receipt.received_at,
    )


def test_customer_regret_return_goes_back_to_sellable_inventory_and_refund():
    product = create_product()
    order = create_order()

    sellable_inventory, quarantine_inventory = create_inventories(product)

    return_item = ReturnItem(
        sku=product.sku,
        quantity=1,
    )

    return_request = ReturnRequest(
        return_id="RETURN-CUSTOMER-001",
        order=order,
        reason=ReturnReason.CUSTOMER_CHANGED_MIND,
        items=[return_item],
        requested_at=datetime(2026, 9, 27, 10, 0, 0),
    )

    receiving_service = ReturnReceivingService()

    return_receipt = receiving_service.receive(
        return_request=return_request,
        sku=product.sku,
        quantity=1,
        receipt_id="RECEIPT-CUSTOMER-001",
        received_at=datetime(2026, 9, 27, 11, 0, 0),
    )

    assert return_receipt.status == ReturnStatus.RECEIVED_AT_WAREHOUSE.value
    assert return_receipt.location == "RETURN_QUARANTINE"

    move_return_to_qc(return_request, return_receipt)

    qc_service = QCService()

    qc_service.record_result(
        return_request=return_request,
        result=QCResult.APPROVED,
        note="Product is healthy and resellable.",
        timestamp=datetime(2026, 9, 27, 12, 0, 0),
    )

    assert return_request.status == ReturnStatus.QC_INSPECTION
    assert return_request.qc_result == QCResult.APPROVED

    state_machine = ReturnStateMachine()

    state_machine.transition(
        return_request,
        ReturnStatus.APPROVED,
        datetime(2026, 9, 27, 12, 30, 0),
    )

    ledger = InventoryLedger()
    inventory_service = InventoryService(ledger=ledger)

    rma_service = RMAService(
        inventory_service=inventory_service,
    )

    returned_batch = rma_service.process(
        return_request=return_request,
        return_receipt=return_receipt,
        order=order,
        sellable_inventory=sellable_inventory,
        quarantine_inventory=quarantine_inventory,
        timestamp=datetime(2026, 9, 27, 13, 0, 0),
        purchase_cost=Decimal("70.00"),
    )

    assert returned_batch is not None
    assert returned_batch.quantity == 1
    assert returned_batch.product.sku == product.sku

    assert sellable_inventory.get_physical_stock(product.sku) == 3
    assert sellable_inventory.get_available_stock(product.sku) == 3

    assert quarantine_inventory.get_physical_stock(product.sku) == 0

    assert len(ledger.transactions) == 1
    assert ledger.transactions[0].transaction_type == (
        InventoryTransactionType.RETURN_TO_STOCK
    )
    assert ledger.transactions[0].quantity == 1

    refund_repository = FinancialTransactionRepository()

    refund_service = RefundService(
        financial_transaction_repository=refund_repository,
    )

    refund = refund_service.refund(
        return_request=return_request,
        order=order,
        timestamp=datetime(2026, 9, 27, 14, 0, 0),
    )

    assert refund.amount == Decimal("100.00")
    assert refund.return_id == return_request.return_id
    assert refund.order_id == order.order_id

    assert return_request.status == ReturnStatus.REFUNDED
    assert return_request.refunded_at == datetime(2026, 9, 27, 14, 0, 0)

    saved_refund = refund_repository.get_by_return_id(
        return_request.return_id
    )

    assert saved_refund is not None
    assert saved_refund.amount == Decimal("100.00")


def test_defective_return_goes_to_scrap_quarantine():
    product = create_product()
    order = create_order()

    sellable_inventory, quarantine_inventory = create_inventories(product)

    return_item = ReturnItem(
        sku=product.sku,
        quantity=1,
    )

    return_request = ReturnRequest(
        return_id="RETURN-DEFECTIVE-001",
        order=order,
        reason=ReturnReason.DAMAGED,
        items=[return_item],
        requested_at=datetime(2026, 9, 27, 10, 0, 0),
    )

    receiving_service = ReturnReceivingService()

    return_receipt = receiving_service.receive(
        return_request=return_request,
        sku=product.sku,
        quantity=1,
        receipt_id="RECEIPT-DEFECTIVE-001",
        received_at=datetime(2026, 9, 27, 11, 0, 0),
    )

    move_return_to_qc(return_request, return_receipt)

    qc_service = QCService()

    qc_service.record_result(
        return_request=return_request,
        result=QCResult.INHERENT_DEFECT,
        note="Product is defective and cannot be resold.",
        timestamp=datetime(2026, 9, 27, 12, 0, 0),
    )

    assert return_request.status == ReturnStatus.QC_INSPECTION
    assert return_request.qc_result == QCResult.INHERENT_DEFECT

    state_machine = ReturnStateMachine()

    state_machine.transition(
        return_request,
        ReturnStatus.APPROVED,
        datetime(2026, 9, 27, 12, 30, 0),
    )

    ledger = InventoryLedger()
    inventory_service = InventoryService(ledger=ledger)

    rma_service = RMAService(
        inventory_service=inventory_service,
    )

    returned_batch = rma_service.process(
        return_request=return_request,
        return_receipt=return_receipt,
        order=order,
        sellable_inventory=sellable_inventory,
        quarantine_inventory=quarantine_inventory,
        timestamp=datetime(2026, 9, 27, 13, 0, 0),
        purchase_cost=Decimal("70.00"),
    )

    assert returned_batch is not None
    assert returned_batch.quantity == 1

    assert sellable_inventory.get_physical_stock(product.sku) == 2
    assert sellable_inventory.get_available_stock(product.sku) == 2

    assert quarantine_inventory.get_physical_stock(product.sku) == 1
    assert quarantine_inventory.get_available_stock(product.sku) == 0

    assert returned_batch.product.sku == product.sku

    assert len(ledger.transactions) == 1
    assert ledger.transactions[0].transaction_type == (
        InventoryTransactionType.SCRAP
    )
    assert ledger.transactions[0].quantity == 1