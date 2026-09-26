from datetime import date, datetime
from decimal import Decimal

from app.domain.enums.inventory_transaction_type import InventoryTransactionType
from app.domain.enums.qc_result import QCResult
from app.domain.enums.return_status import ReturnStatus
from app.domain.enums.warehouse_type import WarehouseType
from app.domain.models.batch import Batch
from app.domain.models.inventory import Inventory
from app.domain.models.inventory_ledger import InventoryLedger
from app.domain.models.order import Order
from app.domain.models.return_receipt import ReturnReceipt
from app.domain.models.return_request import ReturnRequest
from app.domain.models.serialized_unit import SerializedUnit
from app.repositories.product_repository import ProductRepository
from app.services.inventory_service import InventoryService


class RMAService:
    def __init__(
        self,
        inventory_service: InventoryService | None = None,
        product_repository: ProductRepository | None = None,
    ):
        if inventory_service is not None and not isinstance(
            inventory_service,
            InventoryService,
        ):
            raise ValueError(
                "Inventory service must be an InventoryService"
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
                ledger=InventoryLedger()
            )

        if product_repository is None:
            product_repository = ProductRepository()

        self.inventory_service = inventory_service
        self.product_repository = product_repository

    def process(
        self,
        return_request: ReturnRequest,
        return_receipt: ReturnReceipt,
        order: Order,
        sellable_inventory: Inventory,
        quarantine_inventory: Inventory,
        timestamp: datetime | None = None,
        serialized_units: list[SerializedUnit] | None = None,
        purchase_cost: Decimal | None = None,
        expiry_date: date | None = None,
    ) -> Batch | None:
        if timestamp is None:
            timestamp = datetime.now()

        self._validate_inputs(
            return_request=return_request,
            return_receipt=return_receipt,
            order=order,
            sellable_inventory=sellable_inventory,
            quarantine_inventory=quarantine_inventory,
            timestamp=timestamp,
            serialized_units=serialized_units,
            purchase_cost=purchase_cost,
            expiry_date=expiry_date,
        )

        if return_request.qc_result == QCResult.REJECTED:
            if return_request.status != ReturnStatus.REJECTED:
                raise ValueError(
                    "Rejected QC result requires a rejected return request"
                )

            return None

        if return_request.status != ReturnStatus.APPROVED:
            raise ValueError(
                "Return request must be approved before inventory disposition"
            )

        if return_request.qc_result == QCResult.APPROVED:
            target_inventory = sellable_inventory
            target_status = "available"
        elif return_request.qc_result == QCResult.INHERENT_DEFECT:
            target_inventory = quarantine_inventory
            target_status = "quarantine"
        else:
            raise ValueError(
                "QC result is required for inventory disposition"
            )

        if (
            target_inventory.warehouse.warehouse_type
            == WarehouseType.SCRAP_QUARANTINE
        ):
            if target_status == "available":
                raise ValueError(
                    "Approved returns cannot enter a scrap or quarantine warehouse"
                )
        elif target_status == "quarantine":
            raise ValueError(
                "Defective returns must enter a scrap or quarantine warehouse"
            )

        product = self.product_repository.get(
            return_receipt.sku
        )

        if product is None:
            product = self._find_product(
                sku=return_receipt.sku,
                sellable_inventory=sellable_inventory,
                quarantine_inventory=quarantine_inventory,
            )

        if product is None:
            raise ValueError(
                f"Product not found for SKU {return_receipt.sku}"
            )

        historical_cost = self._resolve_purchase_cost(
            order=order,
            sku=return_receipt.sku,
            purchase_cost=purchase_cost,
        )

        batch_id = self._generate_batch_id(
            target_inventory=target_inventory,
            return_id=return_request.return_id,
            sku=return_receipt.sku,
        )

        batch = Batch(
            batch_id=batch_id,
            product=product,
            quantity=return_receipt.quantity,
            entry_date=timestamp.date(),
            expiry_date=expiry_date,
            serial_numbers=(
                list(return_receipt.serial_numbers)
                if return_receipt.serial_numbers is not None
                else None
            ),
            unit_cost=historical_cost,
        )

        original_serial_state = []

        if return_receipt.serial_numbers is not None:
            if serialized_units is None:
                raise ValueError(
                    "Serialized units are required for serialized returns"
                )

            units_by_serial = {
                unit.serial_number: unit
                for unit in serialized_units
            }

            for serial_number in return_receipt.serial_numbers:
                if serial_number not in units_by_serial:
                    raise ValueError(
                        f"Serialized unit {serial_number} was not found"
                    )

                unit = units_by_serial[serial_number]

                if unit.product.sku != return_receipt.sku:
                    raise ValueError(
                        f"Serialized unit {serial_number} does not match SKU "
                        f"{return_receipt.sku}"
                    )

                original_serial_state.append(
                    (
                        unit,
                        unit.location,
                        unit.status,
                    )
                )

        try:
            target_inventory.add_batch(batch)

            for unit, _, _ in original_serial_state:
                unit.location = (
                    target_inventory.warehouse.warehouse_id
                )
                unit.status = target_status

            transaction_type = (
                InventoryTransactionType.RETURN_TO_STOCK
                if target_status == "available"
                else InventoryTransactionType.SCRAP
            )

            self.inventory_service.record_transaction(
                timestamp=timestamp,
                warehouse=target_inventory.warehouse,
                sku=return_receipt.sku,
                quantity=return_receipt.quantity,
                transaction_type=transaction_type,
                reference_id=return_request.return_id,
                batch_id=batch.batch_id,
                serial_numbers=(
                    list(return_receipt.serial_numbers)
                    if return_receipt.serial_numbers is not None
                    else None
                ),
            )

            return batch

        except Exception:
            if batch in target_inventory.batches:
                target_inventory.batches.remove(batch)

            for unit, location, status in original_serial_state:
                unit.location = location
                unit.status = status

            raise

    def _validate_inputs(
        self,
        return_request: ReturnRequest,
        return_receipt: ReturnReceipt,
        order: Order,
        sellable_inventory: Inventory,
        quarantine_inventory: Inventory,
        timestamp: datetime,
        serialized_units: list[SerializedUnit] | None,
        purchase_cost: Decimal | None,
        expiry_date: date | None,
    ) -> None:
        if not isinstance(
            return_request,
            ReturnRequest,
        ):
            raise ValueError(
                "Return request must be a ReturnRequest"
            )

        if not isinstance(
            return_receipt,
            ReturnReceipt,
        ):
            raise ValueError(
                "Return receipt must be a ReturnReceipt"
            )

        if not isinstance(order, Order):
            raise ValueError(
                "Order must be an Order"
            )

        if return_request.order_id != order.order_id:
            raise ValueError(
                "Return request does not belong to the order"
            )

        if (
            return_receipt.return_id
            != return_request.return_id
        ):
            raise ValueError(
                "Return receipt does not belong to the return request"
            )

        if not isinstance(
            sellable_inventory,
            Inventory,
        ):
            raise ValueError(
                "Sellable inventory must be an Inventory"
            )

        if not isinstance(
            quarantine_inventory,
            Inventory,
        ):
            raise ValueError(
                "Quarantine inventory must be an Inventory"
            )

        if (
            sellable_inventory.warehouse.warehouse_id
            == quarantine_inventory.warehouse.warehouse_id
        ):
            raise ValueError(
                "Sellable and quarantine inventories must be different"
            )

        if not isinstance(timestamp, datetime):
            raise ValueError(
                "Timestamp must be a datetime"
            )

        if serialized_units is not None:
            if not isinstance(
                serialized_units,
                list,
            ):
                raise ValueError(
                    "Serialized units must be a list"
                )

            for unit in serialized_units:
                if not isinstance(
                    unit,
                    SerializedUnit,
                ):
                    raise ValueError(
                        "All serialized units must be SerializedUnit instances"
                    )

        if purchase_cost is not None:
            if not isinstance(
                purchase_cost,
                Decimal,
            ):
                raise ValueError(
                    "Purchase cost must be a Decimal"
                )

            if purchase_cost < Decimal("0"):
                raise ValueError(
                    "Purchase cost cannot be negative"
                )

        if expiry_date is not None:
            if not isinstance(
                expiry_date,
                date,
            ):
                raise ValueError(
                    "Expiry date must be a date"
                )

    def _resolve_purchase_cost(
        self,
        order: Order,
        sku: str,
        purchase_cost: Decimal | None,
    ) -> Decimal:
        if purchase_cost is not None:
            return purchase_cost

        for item in order.items:
            if item.sku != sku:
                continue

            if item.unit_price is None:
                raise ValueError(
                    f"Purchase cost is not available for SKU {sku}"
                )

            return item.unit_price

        raise ValueError(
            f"SKU {sku} is not part of the order"
        )

    def _find_product(
        self,
        sku: str,
        sellable_inventory: Inventory,
        quarantine_inventory: Inventory,
    ):
        for inventory in (
            sellable_inventory,
            quarantine_inventory,
        ):
            for batch in inventory.batches:
                if batch.product.sku == sku:
                    return batch.product

        return None

    def _generate_batch_id(
        self,
        target_inventory: Inventory,
        return_id: str,
        sku: str,
    ) -> str:
        prefix = f"RETURN-{return_id}-{sku}"

        existing_ids = {
            batch.batch_id
            for batch in target_inventory.batches
        }

        index = 1
        batch_id = f"{prefix}-{index}"

        while batch_id in existing_ids:
            index += 1
            batch_id = f"{prefix}-{index}"

        return batch_id