from datetime import date, datetime
from decimal import Decimal

from app.domain.enums.qc_result import QCResult
from app.domain.enums.return_reason import ReturnReason
from app.domain.enums.return_status import ReturnStatus
from app.domain.enums.warehouse_type import WarehouseType
from app.domain.models.base_product import BaseProduct
from app.domain.models.batch import Batch
from app.domain.models.inventory import Inventory
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.domain.models.return_item import ReturnItem
from app.domain.models.return_request import ReturnRequest
from app.domain.models.warehouse import Warehouse
from app.domain.states.return_state_machine import ReturnStateMachine
from app.domain.models.inventory_ledger import InventoryLedger
from app.services.inventory_service import InventoryService
from app.services.order_service import OrderService
from app.services.qc_service import QCService
from app.services.refund_service import RefundService
from app.services.return_receiving_service import ReturnReceivingService
from app.services.rma_service import RMAService


def main() -> None:
    timestamp = datetime(2026, 9, 28, 10, 0, 0)

    print("=" * 60)
    print("WMS CORE ENGINE - DEMO")
    print("=" * 60)

    warehouse = Warehouse(
        warehouse_id="WH-001",
        name="Main Warehouse",
        location="Tehran",
        warehouse_type=WarehouseType.CENTRAL,
    )

    quarantine_warehouse = Warehouse(
        warehouse_id="WH-QC-001",
        name="Quarantine Warehouse",
        location="Tehran",
        warehouse_type=WarehouseType.SCRAP_QUARANTINE,
    )

    product = BaseProduct(
        sku="LAPTOP-01",
        name="Laptop",
        barcode="123456789",
        category="Electronics",
        base_price=Decimal("500000"),
    )

    inventory = Inventory(warehouse)
    quarantine_inventory = Inventory(quarantine_warehouse)

    inventory.add_batch(
        Batch(
            batch_id="BATCH-001",
            product=product,
            quantity=10,
            entry_date=date(2026, 9, 1),
            unit_cost=Decimal("350000"),
        )
    )

    print("\n[1] Product and inventory created")
    print(f"SKU: {product.sku}")
    print(f"Product: {product.name}")
    print(f"Stock: {inventory.get_available_stock(product.sku)}")

    order = Order(
        order_id="ORD-001",
        customer_id="CUST-001",
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
        reference_date=date(2026, 9, 28),
        catalog={
            product.sku: product,
        },
    )

    print("\n[2] Order created and stock reserved")
    print(f"Order: {order.order_id}")
    print(f"Status: {order.status.value}")
    print(f"Reservations: {len(reservations)}")
    print(
        f"Available stock: "
        f"{inventory.get_available_stock(product.sku)}"
    )

    payment = order_service.mark_as_paid(
        order=order,
        transaction_reference="TXN-001",
        amount=order.get_total(),
    )

    print("\n[3] Payment completed")
    print(f"Payment: {payment.transaction_id}")
    print(f"Amount: {payment.amount}")
    print(f"Order status: {order.status.value}")

    shipment = order_service.ship_order(
        order=order,
        inventory=inventory,
        timestamp=timestamp,
    )

    print("\n[4] Order shipped")
    print(f"Shipment: {shipment.shipment_id}")
    print(f"Order status: {order.status.value}")
    print(
        f"Available stock: "
        f"{inventory.get_available_stock(product.sku)}"
    )

    order_service.deliver_order(
        order=order,
        timestamp=timestamp,
    )

    print("\n[5] Order delivered")
    print(f"Order status: {order.status.value}")

    return_request = ReturnRequest(
        return_id="RET-001",
        order=order,
        reason=ReturnReason.CUSTOMER_CHANGED_MIND,
        items=[
            ReturnItem(
                sku="LAPTOP-01",
                quantity=1,
            )
        ],
    )

    return_state_machine = ReturnStateMachine()

    print("\n[6] Return request created")
    print(f"Return: {return_request.return_id}")
    print(f"Reason: {return_request.reason.value}")
    print(f"Return status: {return_request.status.value}")

    return_state_machine.transition(
        return_request,
        ReturnStatus.RECEIVED_AT_WAREHOUSE,
        timestamp=timestamp,
    )

    return_receiving_service = ReturnReceivingService()

    return_receipt = return_receiving_service.receive(
        return_request=return_request,
        sku="LAPTOP-01",
        quantity=1,
        receipt_id="RECEIPT-001",
        received_at=timestamp,
    )

    print("\n[7] Return received")
    print(f"Receipt: {return_receipt.receipt_id}")

    return_state_machine.transition(
        return_request,
        ReturnStatus.QC_INSPECTION,
        timestamp=timestamp,
    )

    qc_service = QCService()

    qc_service.record_result(
        return_request=return_request,
        result=QCResult.APPROVED,
        note="Product is healthy and can return to sellable inventory.",
        timestamp=timestamp,
    )

    return_state_machine.transition(
        return_request,
        ReturnStatus.APPROVED,
        timestamp=timestamp,
    )

    print("\n[8] QC completed")
    print(f"QC result: {return_request.qc_result.value}")
    print(f"Return status: {return_request.status.value}")

    inventory_service = InventoryService(
        ledger=InventoryLedger(),
    )

    rma_service = RMAService(
        inventory_service=inventory_service,
    )

    returned_batch = rma_service.process(
        return_request=return_request,
        return_receipt=return_receipt,
        order=order,
        sellable_inventory=inventory,
        quarantine_inventory=quarantine_inventory,
        timestamp=timestamp,
    )

    print("\n[9] RMA processed")
    print(f"Returned batch: {returned_batch.batch_id}")
    print(
        f"Sellable stock: "
        f"{inventory.get_available_stock(product.sku)}"
    )
    print(
        f"Quarantine stock: "
        f"{quarantine_inventory.get_available_stock(product.sku)}"
    )

    refund_service = RefundService()

    refund = refund_service.refund(
        return_request=return_request,
        order=order,
        timestamp=timestamp,
    )

    print("\n[10] Refund completed")
    print(f"Refund: {refund.transaction_id}")
    print(f"Refund amount: {refund.amount}")
    print(f"Return status: {return_request.status.value}")

    print("\n" + "=" * 60)
    print("DEMO COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()