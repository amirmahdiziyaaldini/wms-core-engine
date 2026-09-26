import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from app.domain.enums.financial_transaction_type import FinancialTransactionType
from app.domain.enums.inventory_transaction_type import InventoryTransactionType
from app.domain.enums.order_status import OrderStatus
from app.domain.enums.qc_result import QCResult
from app.domain.enums.return_reason import ReturnReason
from app.domain.enums.return_status import ReturnStatus
from app.domain.enums.transfer_status import TransferStatus
from app.domain.enums.warehouse_type import WarehouseType
from app.domain.models.base_product import BaseProduct
from app.domain.models.batch import Batch
from app.domain.models.bundle_component import BundleComponent
from app.domain.models.bundle_product import BundleProduct
from app.domain.models.financial_transaction import FinancialTransaction
from app.domain.models.inventory import Inventory
from app.domain.models.inventory_ledger import InventoryLedger
from app.domain.models.inventory_transaction import InventoryTransaction
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.domain.models.payment_transaction import PaymentTransaction
from app.domain.models.perishable_product import PerishableProduct
from app.domain.models.reservation import Reservation
from app.domain.models.return_item import ReturnItem
from app.domain.models.return_receipt import ReturnReceipt
from app.domain.models.return_request import ReturnRequest
from app.domain.models.serialized_product import SerializedProduct
from app.domain.models.serialized_unit import SerializedUnit
from app.domain.models.shipment import Shipment
from app.domain.models.stock_transfer import StockTransfer, StockTransferItem
from app.domain.models.variant_product import VariantProduct
from app.domain.models.warehouse import Warehouse


class DeserializationError(ValueError):
    pass


class MissingReferenceError(DeserializationError):
    pass


class DeserializationContext:
    def __init__(self):
        self.products: dict[str, BaseProduct] = {}
        self.warehouses: dict[str, Warehouse] = {}
        self.batches: dict[str, Batch] = {}
        self.orders: dict[str, Order] = {}
        self.returns: dict[str, ReturnRequest] = {}
        self.reservations: dict[str, Reservation] = {}
        self.transfers: dict[str, StockTransfer] = {}
        self.shipments: dict[str, Shipment] = {}
        self.payment_transactions: dict[str, PaymentTransaction] = {}
        self.financial_transactions: dict[str, FinancialTransaction] = {}
        self.serialized_units: dict[str, SerializedUnit] = {}

    def add_product(self, product: BaseProduct) -> None:
        if product.sku in self.products:
            raise DeserializationError(
                f"Duplicate product SKU: {product.sku}"
            )

        self.products[product.sku] = product

    def get_product(self, sku: str) -> BaseProduct:
        try:
            return self.products[sku]
        except KeyError as exc:
            raise MissingReferenceError(
                f"Product reference not found: {sku}"
            ) from exc

    def add_warehouse(self, warehouse: Warehouse) -> None:
        if warehouse.warehouse_id in self.warehouses:
            raise DeserializationError(
                f"Duplicate warehouse ID: {warehouse.warehouse_id}"
            )

        self.warehouses[warehouse.warehouse_id] = warehouse

    def get_warehouse(self, warehouse_id: str) -> Warehouse:
        try:
            return self.warehouses[warehouse_id]
        except KeyError as exc:
            raise MissingReferenceError(
                f"Warehouse reference not found: {warehouse_id}"
            ) from exc

    def add_batch(self, batch: Batch) -> None:
        if batch.batch_id in self.batches:
            raise DeserializationError(
                f"Duplicate batch ID: {batch.batch_id}"
            )

        self.batches[batch.batch_id] = batch

    def get_batch(self, batch_id: str) -> Batch:
        try:
            return self.batches[batch_id]
        except KeyError as exc:
            raise MissingReferenceError(
                f"Batch reference not found: {batch_id}"
            ) from exc

    def add_order(self, order: Order) -> None:
        if order.order_id in self.orders:
            raise DeserializationError(
                f"Duplicate order ID: {order.order_id}"
            )

        self.orders[order.order_id] = order

    def get_order(self, order_id: str) -> Order:
        try:
            return self.orders[order_id]
        except KeyError as exc:
            raise MissingReferenceError(
                f"Order reference not found: {order_id}"
            ) from exc

    def add_return(self, return_request: ReturnRequest) -> None:
        if return_request.return_id in self.returns:
            raise DeserializationError(
                f"Duplicate return ID: {return_request.return_id}"
            )

        self.returns[return_request.return_id] = return_request

    def get_return(self, return_id: str) -> ReturnRequest:
        try:
            return self.returns[return_id]
        except KeyError as exc:
            raise MissingReferenceError(
                f"Return reference not found: {return_id}"
            ) from exc


def deserialize_value(value: Any) -> Any:
    if isinstance(value, list):
        return [deserialize_value(item) for item in value]

    if isinstance(value, dict):
        return {
            key: deserialize_value(item)
            for key, item in value.items()
        }

    return value


def deserialize_decimal(value: Any) -> Decimal:
    if not isinstance(value, str):
        raise DeserializationError(
            "Decimal value must be stored as a string"
        )

    try:
        return Decimal(value)
    except Exception as exc:
        raise DeserializationError(
            f"Invalid Decimal value: {value}"
        ) from exc


def deserialize_datetime(value: Any) -> datetime:
    if not isinstance(value, str):
        raise DeserializationError(
            "Datetime value must be an ISO-8601 string"
        )

    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise DeserializationError(
            f"Invalid datetime value: {value}"
        ) from exc


def deserialize_date(value: Any) -> date:
    if not isinstance(value, str):
        raise DeserializationError(
            "Date value must be an ISO-8601 string"
        )

    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise DeserializationError(
            f"Invalid date value: {value}"
        ) from exc


def deserialize_enum(value: Any, enum_type: type[Enum]) -> Enum:
    try:
        return enum_type(value)
    except (ValueError, TypeError) as exc:
        raise DeserializationError(
            f"Invalid {enum_type.__name__} value: {value}"
        ) from exc


def _require_dict(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise DeserializationError(
            "Entity data must be a dictionary"
        )

    return data


def _required(
    data: dict[str, Any],
    field_name: str,
) -> Any:
    if field_name not in data:
        raise DeserializationError(
            f"Missing field: {field_name}"
        )

    return data[field_name]


def _optional_datetime(
    data: dict[str, Any],
    field_name: str,
) -> datetime | None:
    value = data.get(field_name)

    if value is None:
        return None

    return deserialize_datetime(value)


def _get_product_type(data: dict[str, Any]) -> str:
    product_type = data.get("product_type")

    if product_type is None:
        product_type = data.get("type")

    if not isinstance(product_type, str) or not product_type.strip():
        raise DeserializationError(
            "Product type discriminator is required"
        )

    return product_type


def _build_base_product(
    data: dict[str, Any],
) -> BaseProduct:
    return BaseProduct(
        sku=_required(data, "sku"),
        name=_required(data, "name"),
        barcode=_required(data, "barcode"),
        category=_required(data, "category"),
        base_price=deserialize_decimal(
            _required(data, "base_price")
        ),
    )


def _build_perishable_product(
    data: dict[str, Any],
) -> BaseProduct:
    return PerishableProduct(
        sku=_required(data, "sku"),
        name=_required(data, "name"),
        barcode=_required(data, "barcode"),
        category=_required(data, "category"),
        base_price=deserialize_decimal(
            _required(data, "base_price")
        ),
    )


def _build_serialized_product(
    data: dict[str, Any],
) -> BaseProduct:
    return SerializedProduct(
        sku=_required(data, "sku"),
        name=_required(data, "name"),
        barcode=_required(data, "barcode"),
        category=_required(data, "category"),
        base_price=deserialize_decimal(
            _required(data, "base_price")
        ),
    )


def _build_variant_product(
    data: dict[str, Any],
    context: DeserializationContext,
) -> BaseProduct:
    parent_sku = data.get("parent_product")

    if parent_sku is None:
        parent_sku = _required(
            data,
            "parent_product_sku",
        )

    parent_product = context.get_product(parent_sku)

    return VariantProduct(
        sku=_required(data, "sku"),
        name=_required(data, "name"),
        barcode=_required(data, "barcode"),
        category=_required(data, "category"),
        attributes=data.get("attributes", {}),
        price_modifier=deserialize_decimal(
            _required(data, "price_modifier")
        ),
        parent_product=parent_product,
    )


def _build_bundle_product(
    data: dict[str, Any],
    context: DeserializationContext,
) -> BaseProduct:
    raw_components = _required(
        data,
        "components",
    )

    if not isinstance(raw_components, list) or not raw_components:
        raise DeserializationError(
            "BundleProduct requires a non-empty components list"
        )

    components: list[BundleComponent] = []

    for raw_component in raw_components:
        raw_component = _require_dict(raw_component)

        product_sku = raw_component.get("product")

        if product_sku is None:
            product_sku = raw_component.get(
                "product_sku"
            )

        product = context.get_product(product_sku)

        required_quantity = raw_component.get(
            "required_quantity"
        )

        if (
            isinstance(required_quantity, bool)
            or not isinstance(required_quantity, int)
        ):
            raise DeserializationError(
                "Bundle component required_quantity must be an integer"
            )

        components.append(
            BundleComponent(
                product=product,
                required_quantity=required_quantity,
            )
        )

    return BundleProduct(
        sku=_required(data, "sku"),
        name=_required(data, "name"),
        barcode=_required(data, "barcode"),
        category=_required(data, "category"),
        base_price=deserialize_decimal(
            _required(data, "base_price")
        ),
        components=components,
    )


def deserialize_product(
    data: dict[str, Any],
    context: DeserializationContext,
) -> BaseProduct:
    data = _require_dict(data)

    product_type = _get_product_type(data)

    builders = {
        "BaseProduct": _build_base_product,
        "PerishableProduct": _build_perishable_product,
        "SerializedProduct": _build_serialized_product,
        "VariantProduct": lambda item: _build_variant_product(
            item,
            context,
        ),
        "BundleProduct": lambda item: _build_bundle_product(
            item,
            context,
        ),
    }

    builder = builders.get(product_type)

    if builder is None:
        raise DeserializationError(
            f"Unknown product type: {product_type}"
        )

    try:
        product = builder(data)
    except DeserializationError:
        raise
    except KeyError as exc:
        raise DeserializationError(
            f"Missing product field: {exc.args[0]}"
        ) from exc
    except ValueError as exc:
        raise DeserializationError(
            str(exc)
        ) from exc

    context.add_product(product)

    return product


def _build_warehouse(
    data: dict[str, Any],
    context: DeserializationContext,
) -> Warehouse:
    warehouse = Warehouse(
        warehouse_id=_required(
            data,
            "warehouse_id",
        ),
        name=_required(
            data,
            "name",
        ),
        location=_required(
            data,
            "location",
        ),
        warehouse_type=deserialize_enum(
            _required(
                data,
                "warehouse_type",
            ),
            WarehouseType,
        ),
    )

    context.add_warehouse(warehouse)

    return warehouse


def _build_order_item(
    data: dict[str, Any],
) -> OrderItem:
    unit_price = data.get("unit_price")

    discount = deserialize_decimal(
        data.get("discount", "0")
    )

    return OrderItem(
        item_id=_required(
            data,
            "item_id",
        ),
        sku=_required(
            data,
            "sku",
        ),
        quantity=_required(
            data,
            "quantity",
        ),
        product_name=data.get(
            "product_name"
        ),
        unit_price=(
            deserialize_decimal(unit_price)
            if unit_price is not None
            else None
        ),
        discount=discount,
    )


def _build_reservation(
    data: dict[str, Any],
    context: DeserializationContext,
) -> Reservation:
    reservation = Reservation(
        reservation_id=_required(
            data,
            "reservation_id",
        ),
        order_id=_required(
            data,
            "order_id",
        ),
        order_item_id=_required(
            data,
            "order_item_id",
        ),
        sku=_required(
            data,
            "sku",
        ),
        quantity=_required(
            data,
            "quantity",
        ),
        batch_allocations=data.get(
            "batch_allocations",
            {},
        ),
    )

    context.reservations[
        reservation.reservation_id
    ] = reservation

    return reservation


def _build_order(
    data: dict[str, Any],
    context: DeserializationContext,
) -> Order:
    status = deserialize_enum(
        _required(
            data,
            "status",
        ),
        OrderStatus,
    )

    created_at = deserialize_datetime(
        _required(
            data,
            "created_at",
        )
    )

    order = Order(
        order_id=_required(
            data,
            "order_id",
        ),
        status=status,
        customer_id=data.get(
            "customer_id"
        ),
        created_at=created_at,
    )

    for raw_item in _required(
        data,
        "items",
    ):
        order.add_item(
            _build_order_item(
                _require_dict(raw_item)
            )
        )

    order.reserved_at = _optional_datetime(
        data,
        "reserved_at",
    )

    order.paid_at = _optional_datetime(
        data,
        "paid_at",
    )

    order.shipped_at = _optional_datetime(
        data,
        "shipped_at",
    )

    order.delivered_at = _optional_datetime(
        data,
        "delivered_at",
    )

    order.completed_at = _optional_datetime(
        data,
        "completed_at",
    )

    order.cancelled_at = _optional_datetime(
        data,
        "cancelled_at",
    )

    context.add_order(order)

    return order


def _build_batch(
    data: dict[str, Any],
    context: DeserializationContext,
) -> Batch:
    product = context.get_product(
        _required(
            data,
            "product",
        )
    )

    expiry_date = data.get(
        "expiry_date"
    )

    batch = Batch(
        batch_id=_required(
            data,
            "batch_id",
        ),
        product=product,
        quantity=_required(
            data,
            "quantity",
        ),
        entry_date=deserialize_date(
            _required(
                data,
                "entry_date",
            )
        ),
        expiry_date=(
            deserialize_date(expiry_date)
            if expiry_date is not None
            else None
        ),
        serial_numbers=data.get(
            "serial_numbers"
        ),
        unit_cost=(
            deserialize_decimal(
                data["unit_cost"]
            )
            if data.get("unit_cost") is not None
            else None
        ),
    )

    context.add_batch(batch)

    return batch


def _build_inventory(
    data: dict[str, Any],
    context: DeserializationContext,
) -> Inventory:
    warehouse = context.get_warehouse(
        _required(
            data,
            "warehouse",
        )
    )

    inventory = Inventory(
        warehouse
    )

    for raw_batch in _required(
        data,
        "batches",
    ):
        batch = _build_batch(
            _require_dict(raw_batch),
            context,
        )

        inventory.add_batch(batch)

    raw_reservations = _required(
        data,
        "reservations",
    )

    if not isinstance(
        raw_reservations,
        dict,
    ):
        raise DeserializationError(
            "Inventory reservations must be a dictionary"
        )

    for raw_reservation in raw_reservations.values():
        reservation = _build_reservation(
            _require_dict(
                raw_reservation
            ),
            context,
        )

        inventory.reserve_reservation(
            reservation
        )

    return inventory


def _build_inventory_transaction(
    data: dict[str, Any],
    context: DeserializationContext,
) -> InventoryTransaction:
    return InventoryTransaction(
        timestamp=deserialize_datetime(
            _required(
                data,
                "timestamp",
            )
        ),
        warehouse=context.get_warehouse(
            _required(
                data,
                "warehouse",
            )
        ),
        sku=_required(
            data,
            "sku",
        ),
        quantity=_required(
            data,
            "quantity",
        ),
        transaction_type=deserialize_enum(
            _required(
                data,
                "transaction_type",
            ),
            InventoryTransactionType,
        ),
        reference_id=_required(
            data,
            "reference_id",
        ),
        batch_id=data.get(
            "batch_id"
        ),
        serial_numbers=data.get(
            "serial_numbers",
            [],
        ),
    )


def _build_inventory_ledger(
    data: dict[str, Any],
    context: DeserializationContext,
) -> InventoryLedger:
    ledger = InventoryLedger()

    for raw_transaction in _required(
        data,
        "transactions",
    ):
        transaction = _build_inventory_transaction(
            _require_dict(
                raw_transaction
            ),
            context,
        )

        ledger.record(
            transaction
        )

    return ledger


def _build_bundle_component(
    data: dict[str, Any],
    context: DeserializationContext,
) -> BundleComponent:
    return BundleComponent(
        product=context.get_product(
            data.get(
                "product",
                data.get(
                    "product_sku"
                ),
            )
        ),
        required_quantity=_required(
            data,
            "required_quantity",
        ),
    )


def _build_stock_transfer_item(
    data: dict[str, Any],
) -> StockTransferItem:
    return StockTransferItem(
        sku=_required(
            data,
            "sku",
        ),
        quantity=_required(
            data,
            "quantity",
        ),
        batch_allocations=data.get(
            "batch_allocations",
            {},
        ),
    )


def _build_return_item(
    data: dict[str, Any],
) -> ReturnItem:
    return ReturnItem(
        sku=_required(
            data,
            "sku",
        ),
        quantity=_required(
            data,
            "quantity",
        ),
        serial_numbers=data.get(
            "serial_numbers"
        ),
    )


def _build_stock_transfer(
    data: dict[str, Any],
    context: DeserializationContext,
) -> StockTransfer:
    transfer = StockTransfer(
        transfer_id=_required(
            data,
            "transfer_id",
        ),
        source=context.get_warehouse(
            _required(
                data,
                "source",
            )
        ),
        destination=context.get_warehouse(
            _required(
                data,
                "destination",
            )
        ),
        items=[
            _build_stock_transfer_item(
                _require_dict(item)
            )
            for item in _required(
                data,
                "items",
            )
        ],
        created_at=deserialize_datetime(
            _required(
                data,
                "created_at",
            )
        ),
        dispatched_at=_optional_datetime(
            data,
            "dispatched_at",
        ),
        received_at=_optional_datetime(
            data,
            "received_at",
        ),
        status=deserialize_enum(
            _required(
                data,
                "status",
            ),
            TransferStatus,
        ),
    )

    context.transfers[
        transfer.transfer_id
    ] = transfer

    return transfer


def _build_return_request(
    data: dict[str, Any],
    context: DeserializationContext,
) -> ReturnRequest:
    order = context.get_order(
        _required(
            data,
            "order_id",
        )
    )

    items = [
        _build_return_item(
            _require_dict(item)
        )
        for item in _required(
            data,
            "items",
        )
    ]

    return_request = ReturnRequest(
        return_id=_required(
            data,
            "return_id",
        ),
        order=order,
        reason=deserialize_enum(
            _required(
                data,
                "reason",
            ),
            ReturnReason,
        ),
        items=items,
        requested_at=deserialize_datetime(
            _required(
                data,
                "requested_at",
            )
        ),
    )

    return_request._status = deserialize_enum(
        _required(
            data,
            "status",
        ),
        ReturnStatus,
    )

    return_request.received_at_warehouse = _optional_datetime(
        data,
        "received_at_warehouse",
    )

    return_request.qc_inspection_at = _optional_datetime(
        data,
        "qc_inspection_at",
    )

    return_request.approved_at = _optional_datetime(
        data,
        "approved_at",
    )

    return_request.rejected_at = _optional_datetime(
        data,
        "rejected_at",
    )

    return_request.refunded_at = _optional_datetime(
        data,
        "refunded_at",
    )

    qc_result = data.get(
        "qc_result"
    )

    if qc_result is not None:
        return_request.qc_result = deserialize_enum(
            qc_result,
            QCResult,
        )

    return_request.qc_note = data.get(
        "qc_note"
    )

    return_request.qc_at = _optional_datetime(
        data,
        "qc_at",
    )

    context.add_return(
        return_request
    )

    return return_request


def _build_return_receipt(
    data: dict[str, Any],
) -> ReturnReceipt:
    return ReturnReceipt(
        receipt_id=_required(
            data,
            "receipt_id",
        ),
        return_id=_required(
            data,
            "return_id",
        ),
        sku=_required(
            data,
            "sku",
        ),
        quantity=_required(
            data,
            "quantity",
        ),
        serial_numbers=data.get(
            "serial_numbers"
        ),
        location=data.get(
            "location",
            "RETURN_QUARANTINE",
        ),
        status=data.get(
            "status",
            "received_at_warehouse",
        ),
        received_at=_optional_datetime(
            data,
            "received_at",
        ),
    )


def _build_serialized_unit(
    data: dict[str, Any],
    context: DeserializationContext,
) -> SerializedUnit:
    product = context.get_product(
        _required(
            data,
            "product",
        )
    )

    if not isinstance(
        product,
        SerializedProduct,
    ):
        raise DeserializationError(
            "SerializedUnit requires a SerializedProduct"
        )

    unit = SerializedUnit(
        serial_number=_required(
            data,
            "serial_number",
        ),
        product=product,
        location=data.get(
            "location"
        ),
        status=data.get(
            "status",
            "available",
        ),
    )

    context.serialized_units[
        unit.serial_number
    ] = unit

    return unit


def _build_shipment(
    data: dict[str, Any],
    context: DeserializationContext,
) -> Shipment:
    shipment = Shipment(
        shipment_id=_required(
            data,
            "shipment_id",
        ),
        order_id=_required(
            data,
            "order_id",
        ),
        warehouse_id=_required(
            data,
            "warehouse_id",
        ),
        shipped_at=deserialize_datetime(
            _required(
                data,
                "shipped_at",
            )
        ),
        serial_numbers=data.get(
            "serial_numbers",
            [],
        ),
        delivered_at=_optional_datetime(
            data,
            "delivered_at",
        ),
    )

    context.shipments[
        shipment.shipment_id
    ] = shipment

    return shipment


def _build_payment_transaction(
    data: dict[str, Any],
    context: DeserializationContext,
) -> PaymentTransaction:
    transaction = PaymentTransaction(
        transaction_id=_required(
            data,
            "transaction_id",
        ),
        order_id=_required(
            data,
            "order_id",
        ),
        reference=_required(
            data,
            "reference",
        ),
        amount=deserialize_decimal(
            _required(
                data,
                "amount",
            )
        ),
        created_at=_optional_datetime(
            data,
            "created_at",
        ),
    )

    context.payment_transactions[
        transaction.transaction_id
    ] = transaction

    return transaction


def _build_financial_transaction(
    data: dict[str, Any],
    context: DeserializationContext,
) -> FinancialTransaction:
    raw_type = data.get(
        "transaction_type",
        data.get("type"),
    )

    transaction = FinancialTransaction(
        transaction_id=_required(
            data,
            "transaction_id",
        ),
        return_id=_required(
            data,
            "return_id",
        ),
        order_id=_required(
            data,
            "order_id",
        ),
        amount=deserialize_decimal(
            _required(
                data,
                "amount",
            )
        ),
        transaction_type=deserialize_enum(
            raw_type,
            FinancialTransactionType,
        ),
        timestamp=_optional_datetime(
            data,
            "timestamp",
        ),
    )

    context.financial_transactions[
        transaction.transaction_id
    ] = transaction

    return transaction


def deserialize_entity(
    data: dict[str, Any],
    context: DeserializationContext | None = None,
) -> Any:
    data = _require_dict(data)

    if context is None:
        context = DeserializationContext()

    entity_type = data.get(
        "type"
    )

    try:
        if (
            data.get("product_type") is not None
            or entity_type in {
                "BaseProduct",
                "VariantProduct",
                "BundleProduct",
                "PerishableProduct",
                "SerializedProduct",
            }
        ):
            return deserialize_product(
                data,
                context,
            )

        builders = {
            "Warehouse": _build_warehouse,
            "Batch": _build_batch,
            "BundleComponent": _build_bundle_component,
            "OrderItem": lambda item, _context: _build_order_item(
                item
            ),
            "Reservation": _build_reservation,
            "ReturnItem": lambda item, _context: _build_return_item(
                item
            ),
            "StockTransferItem": lambda item, _context: _build_stock_transfer_item(
                item
            ),
            "Order": _build_order,
            "Inventory": _build_inventory,
            "InventoryTransaction": _build_inventory_transaction,
            "InventoryLedger": _build_inventory_ledger,
            "StockTransfer": _build_stock_transfer,
            "ReturnRequest": _build_return_request,
            "ReturnReceipt": _build_return_receipt,
            "SerializedUnit": _build_serialized_unit,
            "Shipment": _build_shipment,
            "PaymentTransaction": _build_payment_transaction,
            "FinancialTransaction": _build_financial_transaction,
            "refund": _build_financial_transaction,
        }

        builder = builders.get(
            entity_type
        )

        if builder is None:
            raise DeserializationError(
                f"Unknown entity type: {entity_type}"
            )

        return builder(
            data,
            context,
        )

    except DeserializationError:
        raise

    except (KeyError, TypeError, ValueError) as exc:
        raise DeserializationError(
            f"Could not deserialize {entity_type}: {exc}"
        ) from exc


def load_entities(
    data: list[dict[str, Any]],
    context: DeserializationContext | None = None,
) -> list[Any]:
    if not isinstance(
        data,
        list,
    ):
        raise DeserializationError(
            "Entities data must be a list"
        )

    if context is None:
        context = DeserializationContext()

    pending = list(data)
    loaded: list[Any] = []

    while pending:
        progress = False
        remaining: list[dict[str, Any]] = []

        for item in pending:
            try:
                loaded.append(
                    deserialize_entity(
                        item,
                        context,
                    )
                )

                progress = True

            except MissingReferenceError:
                remaining.append(item)

        if not progress:
            references = []

            for item in remaining:
                references.append(
                    f"{item.get('type', 'unknown')}:"
                    f"{item.get('sku', item.get('order_id', 'unknown'))}"
                )

            raise DeserializationError(
                "Unable to resolve entity references: "
                + ", ".join(references)
            )

        pending = remaining

    return loaded


def load_products(
    data: list[dict[str, Any]],
    context: DeserializationContext | None = None,
) -> list[BaseProduct]:
    return [
        product
        for product in load_entities(
            data,
            context,
        )
        if isinstance(
            product,
            BaseProduct,
        )
    ]


def from_json(
    value: str,
    context: DeserializationContext | None = None,
) -> Any:
    if not isinstance(
        value,
        str,
    ):
        raise DeserializationError(
            "JSON value must be a string"
        )

    try:
        data = json.loads(value)

    except json.JSONDecodeError as exc:
        raise DeserializationError(
            "Invalid JSON"
        ) from exc

    return deserialize_entity(
        data,
        context,
    )