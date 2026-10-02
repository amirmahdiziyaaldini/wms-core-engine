import json
import os
import tempfile
import threading
import time
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
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
from app.serialization.serializer import serialize_entity


SNAPSHOT_VERSION = 1


SECTIONS = (
    "products",
    "warehouses",
    "inventories",
    "orders",
    "returns",
    "transfers",
    "inventory_logs",
    "return_receipts",
    "serialized_units",
    "shipments",
    "payment_transactions",
    "financial_logs",
)

SECTION_IDENTIFIER_FIELDS = {
    "products": "sku",
    "warehouses": "warehouse_id",
    "inventories": "warehouse",
    "orders": "order_id",
    "returns": "return_id",
    "transfers": "transfer_id",
    "return_receipts": "receipt_id",
    "serialized_units": "serial_number",
    "shipments": "shipment_id",
    "payment_transactions": "transaction_id",
    "financial_logs": "transaction_id",
}


REFERENCE_FIELDS = {
    "product": "products",
    "parent_product": "products",
    "warehouse": "warehouses",
    "source": "warehouses",
    "destination": "warehouses",
    "order": "orders",
}


CLASS_REGISTRY = {
    "BaseProduct": BaseProduct,
    "VariantProduct": VariantProduct,
    "BundleProduct": BundleProduct,
    "PerishableProduct": PerishableProduct,
    "SerializedProduct": SerializedProduct,
    "BundleComponent": BundleComponent,
    "Warehouse": Warehouse,
    "Batch": Batch,
    "Inventory": Inventory,
    "Reservation": Reservation,
    "InventoryTransaction": InventoryTransaction,
    "InventoryLedger": InventoryLedger,
    "Order": Order,
    "OrderItem": OrderItem,
    "StockTransferItem": StockTransferItem,
    "StockTransfer": StockTransfer,
    "ReturnItem": ReturnItem,
    "ReturnRequest": ReturnRequest,
    "ReturnReceipt": ReturnReceipt,
    "SerializedUnit": SerializedUnit,
    "Shipment": Shipment,
    "PaymentTransaction": PaymentTransaction,
    "FinancialTransaction": FinancialTransaction,
}


DECIMAL_FIELDS = {
    "base_price",
    "price_modifier",
    "unit_cost",
    "amount",
    "unit_price",
    "discount",
    "line_total",
}


DATE_FIELDS = {
    "entry_date",
    "expiry_date",
}


ENUM_FIELDS = {
    "warehouse_type": WarehouseType,
    "reason": ReturnReason,
    "qc_result": QCResult,
    "transaction_type": InventoryTransactionType,
}


def build_snapshot(state: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(state, dict):
        raise ValueError(
            "Snapshot state must be a dictionary"
        )

    snapshot = {
        "version": SNAPSHOT_VERSION,
    }

    for section in SECTIONS:
        entities = state.get(
            section,
            [],
        )

        if not isinstance(entities, list):
            raise ValueError(
                f"Snapshot section '{section}' must be a list"
            )

        serialized_entities = [
            serialize_entity(entity)
            for entity in entities
        ]

        seen_identifiers: set[str] = set()
        identifier_field = SECTION_IDENTIFIER_FIELDS.get(section)

        for entity in serialized_entities:
            if identifier_field is None:
                continue

            identifier = entity.get(identifier_field)
            if section == "inventories" and isinstance(identifier, dict):
                identifier = identifier.get("warehouse_id")

            if not isinstance(identifier, str) or not identifier.strip():
                raise ValueError(
                    f"Missing identifier for snapshot section '{section}'"
                )

            if identifier in seen_identifiers:
                raise ValueError(
                    f"Duplicate snapshot identifier: {section} '{identifier}'"
                )

            seen_identifiers.add(identifier)

        snapshot[section] = serialized_entities

    return snapshot


def save_snapshot(
    file_path: str | Path,
    state: dict[str, Any],
) -> None:
    path = Path(file_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    snapshot = build_snapshot(state)

    temporary_path = None

    try:
        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
        )
        temporary_path = Path(temporary_name)

        with os.fdopen(
            file_descriptor,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                snapshot,
                file,
                ensure_ascii=False,
                indent=4,
            )

            file.flush()
            os.fsync(
                file.fileno()
            )

        with _SNAPSHOT_SAVE_LOCK:
            last_error = None

            for _ in range(20):
                try:
                    os.replace(
                        temporary_path,
                        path,
                    )
                    temporary_path = None
                    break
                except PermissionError as exc:
                    last_error = exc
                    time.sleep(0.01)

            if temporary_path is not None:
                raise last_error

    except OSError as exc:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()

        raise ValueError(
            f"Could not save snapshot: {path}"
        ) from exc


def _validate_snapshot(
    data: Any,
) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError(
            "Snapshot root must be a JSON object"
        )

    if data.get("version") != SNAPSHOT_VERSION:
        raise ValueError(
            f"Unsupported snapshot version: "
            f"{data.get('version')}"
        )

    for section in SECTIONS:
        if section not in data:
            raise ValueError(
                f"Missing snapshot section: {section}"
            )

        if not isinstance(
            data[section],
            list,
        ):
            raise ValueError(
                f"Snapshot section '{section}' "
                f"must be a list"
            )

        identifier_field = SECTION_IDENTIFIER_FIELDS.get(section)
        if identifier_field is not None:
            seen_identifiers: set[str] = set()
            for entity in data[section]:
                if not isinstance(entity, dict):
                    raise ValueError(
                        f"Snapshot entity in '{section}' must be a JSON object"
                    )
                identifier = entity.get(identifier_field)
                if section == "inventories" and isinstance(identifier, dict):
                    identifier = identifier.get("warehouse_id")
                if not isinstance(identifier, str) or not identifier.strip():
                    raise ValueError(
                        f"Missing identifier in snapshot section '{section}'"
                    )
                if identifier in seen_identifiers:
                    raise ValueError(
                        f"Duplicate snapshot identifier: {section} '{identifier}'"
                    )
                seen_identifiers.add(identifier)

    return data


class SnapshotContext:

    def __init__(self):
        self.objects = {
            "products": {},
            "warehouses": {},
            "orders": {},
        }

    def add(
        self,
        section: str,
        key: str,
        obj: Any,
    ) -> None:
        if key in self.objects[section]:
            raise ValueError(
                f"Duplicate snapshot identifier: {section} '{key}'"
            )

        self.objects[section][key] = obj

    def get(
        self,
        section: str,
        key: str,
    ) -> Any:
        if key not in self.objects[section]:
            raise ValueError(
                f"Reference not found: "
                f"{section} '{key}'"
            )

        return self.objects[section][key]


def _object_key(
    data: dict[str, Any],
) -> tuple[str, str] | None:

    entity_type = data.get(
        "type"
    )

    if entity_type in {
        "BaseProduct",
        "VariantProduct",
        "BundleProduct",
        "PerishableProduct",
        "SerializedProduct",
    }:
        return (
            "products",
            data.get(
                "sku",
                "",
            ),
        )

    if entity_type == "Warehouse":
        return (
            "warehouses",
            data.get(
                "warehouse_id",
                "",
            ),
        )

    if entity_type == "Order":
        return (
            "orders",
            data.get(
                "order_id",
                "",
            ),
        )

    return None


def _prepare_root_objects(
    section: list[dict[str, Any]],
    context: SnapshotContext,
) -> None:

    for data in section:

        if not isinstance(
            data,
            dict,
        ):
            raise ValueError(
                "Snapshot entity must be a JSON object"
            )

        key_info = _object_key(
            data
        )

        if key_info is None:
            continue

        section_name, key = key_info

        entity_type = data.get(
            "type"
        )

        if not key:
            raise ValueError(
                f"Missing identifier for "
                f"{entity_type}"
            )

        if entity_type not in CLASS_REGISTRY:
            raise ValueError(
                f"Unknown entity type: "
                f"{entity_type}"
            )

        obj = CLASS_REGISTRY[
            entity_type
        ].__new__(
            CLASS_REGISTRY[
                entity_type
            ]
        )

        context.add(
            section_name,
            key,
            obj,
        )


def _enum_for_field(
    field_name: str,
    owner_type: str,
) -> type[Enum] | None:

    if field_name == "status":

        if owner_type == "Order":
            return OrderStatus

        if owner_type == "ReturnRequest":
            return ReturnStatus

        if owner_type == "StockTransfer":
            return TransferStatus

    if field_name == "transaction_type":

        if owner_type == "FinancialTransaction":
            return FinancialTransactionType

        return InventoryTransactionType

    return ENUM_FIELDS.get(
        field_name
    )


def _restore_value(
    value: Any,
    field_name: str,
    owner_type: str,
    context: SnapshotContext,
) -> Any:

    if isinstance(
        value,
        list,
    ):
        return [
            _restore_value(
                item,
                field_name,
                owner_type,
                context,
            )
            for item in value
        ]

    if isinstance(
        value,
        dict,
    ):

        if (
            "type" in value
            and value["type"] in CLASS_REGISTRY
        ):
            return _restore_entity(
                value,
                context,
            )

        return {
            key: _restore_value(
                item,
                key,
                owner_type,
                context,
            )
            for key, item in value.items()
        }

    if isinstance(
        value,
        str,
    ):

        reference_section = REFERENCE_FIELDS.get(
            field_name
        )

        if reference_section is not None:
            return context.get(
                reference_section,
                value,
            )

        enum_type = _enum_for_field(
            field_name,
            owner_type,
        )

        if enum_type is not None:
            return enum_type(
                value
            )

        if field_name in DECIMAL_FIELDS:
            return Decimal(
                value
            )

        if field_name in DATE_FIELDS:
            return date.fromisoformat(
                value
            )

        if (
            field_name.endswith("_at")
            or field_name in {
                "timestamp",
                "created_at",
                "dispatched_at",
                "received_at",
            }
        ):
            return datetime.fromisoformat(
                value
            )

    return value


def _attribute_name(
    field_name: str,
    owner_type: str,
) -> str:

    if (
        owner_type in {
            "Order",
            "ReturnRequest",
        }
        and field_name == "status"
    ):
        return "_status"

    if owner_type == "OrderItem":

        private_fields = {
            "unit_price": "_unit_price",
            "discount": "_discount",
            "line_total": "_line_total",
        }

        if field_name in private_fields:
            return private_fields[
                field_name
            ]

    if (
        owner_type == "FinancialTransaction"
        and field_name == "transaction_type"
    ):
        return "type"

    return field_name


STRING_FIELDS = {
    "sku",
    "name",
    "barcode",
    "category",
    "warehouse_id",
    "batch_id",
    "product_sku",
    "reservation_id",
    "order_id",
    "order_item_id",
    "item_id",
    "customer_id",
    "reference_id",
    "transfer_id",
    "return_id",
    "receipt_id",
    "location",
    "reason",
    "qc_note",
    "serial_number",
    "shipment_id",
    "reference",
    "transaction_id",
    "status",
}

INTEGER_FIELDS = {
    "quantity",
    "original_quantity",
    "remaining_quantity",
    "required_quantity",
}

LIST_FIELDS = {
    "serial_numbers",
    "components",
    "batches",
    "items",
    "transactions",
    "return_receipts",
    "serialized_units",
    "shipments",
    "payment_transactions",
    "financial_logs",
    "inventory_logs",
    "transfers",
    "previous_returns",
}

DICT_FIELDS = {
    "attributes",
    "batch_allocations",
    "serial_allocations",
}

REQUIRED_FIELDS = {
    "BaseProduct": {"sku", "name", "barcode", "category", "base_price"},
    "VariantProduct": {"sku", "name", "barcode", "category", "attributes", "price_modifier"},
    "BundleProduct": {"sku", "name", "barcode", "category", "base_price", "components"},
    "PerishableProduct": {"sku", "name", "barcode", "category", "base_price"},
    "SerializedProduct": {"sku", "name", "barcode", "category", "base_price"},
    "BundleComponent": {"product", "required_quantity"},
    "Warehouse": {"warehouse_id", "name", "location", "warehouse_type"},
    "Batch": {"batch_id", "product", "original_quantity", "remaining_quantity", "entry_date"},
    "Inventory": {"warehouse", "batches", "reservations"},
    "Reservation": {"reservation_id", "order_id", "order_item_id", "sku", "quantity", "batch_allocations"},
    "InventoryTransaction": {"timestamp", "warehouse", "sku", "quantity", "transaction_type", "reference_id"},
    "Order": {"order_id", "status", "customer_id", "created_at", "items"},
    "OrderItem": {"item_id", "sku", "quantity", "product_name", "unit_price", "discount", "line_total"},
    "StockTransferItem": {"sku", "quantity", "batch_allocations", "serial_allocations"},
    "StockTransfer": {"transfer_id", "source", "destination", "items", "created_at", "status"},
    "ReturnItem": {"sku", "quantity"},
    "ReturnRequest": {"return_id", "order_id", "reason", "items", "status", "requested_at"},
    "ReturnReceipt": {"receipt_id", "return_id", "sku", "quantity", "serial_numbers", "location", "status", "received_at"},
    "SerializedUnit": {"serial_number", "product", "location", "status"},
    "Shipment": {"shipment_id", "order_id", "warehouse_id", "shipped_at", "serial_numbers", "delivered_at"},
    "PaymentTransaction": {"transaction_id", "order_id", "reference", "amount", "created_at"},
    "FinancialTransaction": {"transaction_id", "return_id", "order_id", "amount", "transaction_type", "timestamp"},
}

_SNAPSHOT_SAVE_LOCK = threading.Lock()

OPTIONAL_STRING_FIELDS = {
    "customer_id",
    "product_name",
    "qc_note",
    "location",
    "status",
    "batch_id",
    "product_sku",
    "order_item_id",
}

def _validate_restored_entity(
    data: dict[str, Any],
    entity_type: str,
) -> None:
    required_fields = REQUIRED_FIELDS.get(entity_type)
    if required_fields is None:
        raise ValueError(f"Unknown entity type: {entity_type}")

    missing_fields = required_fields.difference(data.keys())
    if entity_type == "VariantProduct" and "parent_product" not in data and "parent_product_sku" not in data:
        missing_fields.add("parent_product")
    if missing_fields:
        raise ValueError(
            f"Missing required snapshot fields for {entity_type}: "
            + ", ".join(sorted(missing_fields))
        )

    for field_name, value in data.items():
        if field_name == "type":
            continue

        if field_name in DECIMAL_FIELDS:
            if value is None:
                continue
            if not isinstance(value, str):
                raise ValueError(
                    f"Invalid Decimal field '{field_name}' in {entity_type}"
                )
            try:
                Decimal(value)
            except Exception as exc:
                raise ValueError(
                    f"Invalid Decimal field '{field_name}' in {entity_type}"
                ) from exc
            continue

        if field_name in DATE_FIELDS:
            if value is not None:
                if not isinstance(value, str):
                    raise ValueError(
                        f"Invalid date field '{field_name}' in {entity_type}"
                    )
                try:
                    date.fromisoformat(value)
                except ValueError as exc:
                    raise ValueError(
                        f"Invalid date field '{field_name}' in {entity_type}"
                    ) from exc
            continue

        if field_name.endswith("_at") or field_name in {
            "timestamp",
            "created_at",
            "dispatched_at",
            "received_at",
            "shipped_at",
            "delivered_at",
        }:
            if value is not None and not isinstance(value, str):
                raise ValueError(
                    f"Invalid datetime field '{field_name}' in {entity_type}"
                )
            if isinstance(value, str):
                try:
                    datetime.fromisoformat(value)
                except ValueError as exc:
                    raise ValueError(
                        f"Invalid datetime field '{field_name}' in {entity_type}"
                    ) from exc
            continue

        if field_name in INTEGER_FIELDS:
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError(
                    f"Invalid integer field '{field_name}' in {entity_type}"
                )
            continue

        if field_name in LIST_FIELDS:
            if value is not None and not isinstance(value, list):
                raise ValueError(
                    f"Invalid list field '{field_name}' in {entity_type}"
                )
            continue

        if field_name in DICT_FIELDS:
            if value is not None and not isinstance(value, dict):
                raise ValueError(
                    f"Invalid dictionary field '{field_name}' in {entity_type}"
                )
            continue

        if entity_type == "Inventory" and field_name == "reservations":
            if not isinstance(value, dict):
                raise ValueError(
                    "Invalid reservations field in Inventory"
                )
            continue

        if field_name in STRING_FIELDS or field_name in OPTIONAL_STRING_FIELDS:
            if value is not None and not isinstance(value, str):
                raise ValueError(
                    f"Invalid string field '{field_name}' in {entity_type}"
                )

    identifier_fields = {
        "BaseProduct": "sku",
        "VariantProduct": "sku",
        "BundleProduct": "sku",
        "PerishableProduct": "sku",
        "SerializedProduct": "sku",
        "Warehouse": "warehouse_id",
        "Batch": "batch_id",
        "Order": "order_id",
        "Reservation": "reservation_id",
        "StockTransfer": "transfer_id",
        "ReturnRequest": "return_id",
        "ReturnReceipt": "receipt_id",
        "SerializedUnit": "serial_number",
        "Shipment": "shipment_id",
        "PaymentTransaction": "transaction_id",
        "FinancialTransaction": "transaction_id",
    }

    identifier_field = identifier_fields.get(entity_type)
    if identifier_field is not None:
        identifier = data.get(identifier_field)
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError(
                f"{entity_type} identifier cannot be empty"
            )

    if entity_type in {
        "BaseProduct",
        "BundleProduct",
        "PerishableProduct",
        "SerializedProduct",
    }:
        if Decimal(data["base_price"]) < 0:
            raise ValueError("Base price cannot be negative")

    if entity_type == "VariantProduct":
        if Decimal(data["price_modifier"]) < 0:
            raise ValueError("Price modifier cannot be negative")

    if entity_type == "BundleComponent":
        required_quantity = data.get("required_quantity")
        if not isinstance(required_quantity, int) or isinstance(required_quantity, bool) or required_quantity <= 0:
            raise ValueError("Invalid required quantity")

    if entity_type == "Batch":
        original_quantity = data.get("original_quantity")
        remaining_quantity = data.get("remaining_quantity")
        if not isinstance(original_quantity, int) or isinstance(original_quantity, bool) or original_quantity <= 0:
            raise ValueError("Invalid batch original quantity")
        if not isinstance(remaining_quantity, int) or isinstance(remaining_quantity, bool) or remaining_quantity < 0 or remaining_quantity > original_quantity:
            raise ValueError("Invalid batch remaining quantity")
        if data.get("unit_cost") is not None and Decimal(data["unit_cost"]) < 0:
            raise ValueError("Unit cost cannot be negative")

    if entity_type in {"OrderItem", "Reservation", "StockTransferItem", "ReturnItem", "ReturnReceipt"}:
        quantity = data.get("quantity")
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
            raise ValueError(f"Invalid quantity in {entity_type}")

    if entity_type == "OrderItem":
        discount = data.get("discount")
        if discount is not None and Decimal(discount) < 0:
            raise ValueError("Order item discount cannot be negative")

    if entity_type == "PaymentTransaction" and Decimal(data["amount"]) <= 0:
        raise ValueError("Payment amount must be positive")

    if entity_type == "FinancialTransaction" and Decimal(data["amount"]) <= 0:
        raise ValueError("Financial transaction amount must be positive")

    if entity_type in {"Order", "ReturnRequest", "StockTransfer"}:
        status = data.get("status")
        if not isinstance(status, str) or not status.strip():
            raise ValueError(f"Invalid status in {entity_type}")

    if entity_type == "Reservation":
        quantity = data.get("quantity")
        allocations = data.get("batch_allocations", {})

        total_allocated = sum(allocations.values())

        if allocations and total_allocated != quantity:
            raise ValueError(
                "Reservation batch allocations do not match reservation quantity"
            )

    if entity_type == "OrderItem":
        unit_price = data.get("unit_price")
        discount = data.get("discount")
        quantity = data.get("quantity")

        if unit_price is not None and discount is not None:
            if Decimal(discount) > Decimal(unit_price) * quantity:
                raise ValueError("Order item discount exceeds gross total")


def _restore_entity(
    data: dict[str, Any],
    context: SnapshotContext,
) -> Any:

    entity_type = data.get(
        "type"
    )

    if entity_type not in CLASS_REGISTRY:
        raise ValueError(
            f"Unknown entity type: "
            f"{entity_type}"
        )

    _validate_restored_entity(data, entity_type)

    key_info = _object_key(
        data
    )

    if key_info is not None:

        section_name, key = key_info

        obj = context.get(
            section_name,
            key,
        )

    else:

        obj = CLASS_REGISTRY[
            entity_type
        ].__new__(
            CLASS_REGISTRY[
                entity_type
            ]
        )

    for field_name, value in data.items():

        if field_name == "type":
            continue

        attribute_name = _attribute_name(
            field_name,
            entity_type,
        )

        restored_value = _restore_value(
            value,
            field_name,
            entity_type,
            context,
        )

        setattr(
            obj,
            attribute_name,
            restored_value,
        )

    return obj


def _load_section(
    section: list[dict[str, Any]],
    context: SnapshotContext,
) -> list[Any]:

    _prepare_root_objects(
        section,
        context,
    )

    return [
        _restore_entity(
            item,
            context,
        )
        for item in section
    ]


def _validate_loaded_graph(
    result: dict[str, list[Any]],
) -> None:
    orders = {
        order.order_id: order
        for order in result["orders"]
        if isinstance(order, Order)
    }

    for inventory in result["inventories"]:
        if not isinstance(inventory, Inventory):
            continue

        batches_by_id = {
            batch.batch_id: batch
            for batch in inventory.batches
        }

        for reservation in inventory.reservations.values():
            if not isinstance(reservation, Reservation):
                raise ValueError("Invalid reservation in snapshot")

            order = orders.get(reservation.order_id)
            if order is None:
                raise ValueError(
                    f"Reservation references unknown order: {reservation.order_id}"
                )

            matching_items = [
                item
                for item in order.items
                if item.item_id == reservation.order_item_id
            ]

            if not matching_items:
                raise ValueError(
                    f"Reservation references unknown order item: {reservation.order_item_id}"
                )

            if matching_items[0].sku != reservation.sku:
                raise ValueError(
                    "Reservation SKU does not match order item SKU"
                )

            if reservation.batch_allocations:
                if sum(reservation.batch_allocations.values()) != reservation.quantity:
                    raise ValueError(
                        "Reservation batch allocations do not match reservation quantity"
                    )

                for batch_id, quantity in reservation.batch_allocations.items():
                    batch = batches_by_id.get(batch_id)
                    if batch is None:
                        raise ValueError(
                            f"Reservation references unknown batch: {batch_id}"
                        )

                    if batch.product.sku != reservation.sku:
                        raise ValueError(
                            "Reservation batch SKU does not match reservation SKU"
                        )

                    if batch.warehouse_id != inventory.warehouse.warehouse_id:
                        raise ValueError(
                            "Reservation batch warehouse does not match inventory warehouse"
                        )

                    if quantity > batch.quantity:
                        raise ValueError(
                            f"Reservation allocation exceeds batch stock: {batch_id}"
                        )


def load_snapshot(
    file_path: str | Path,
) -> dict[str, list[Any]]:

    path = Path(
        file_path
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Snapshot file not found: {path}"
        )

    try:

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(
                file
            )

    except json.JSONDecodeError as exc:

        raise ValueError(
            f"Invalid snapshot JSON: {path}"
        ) from exc

    except OSError as exc:

        raise ValueError(
            f"Could not read snapshot: {path}"
        ) from exc

    data = _validate_snapshot(
        data
    )

    context = SnapshotContext()

    result = {}

    for section in SECTIONS:

        result[section] = _load_section(
            data[section],
            context,
        )

    _validate_loaded_graph(result)

    return result