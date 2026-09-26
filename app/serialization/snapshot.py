import json
import os
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

        snapshot[section] = [
            serialize_entity(entity)
            for entity in entities
        ]

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

    temporary_path = path.with_suffix(
        path.suffix + ".tmp"
    )

    try:
        with temporary_path.open(
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

        os.replace(
            temporary_path,
            path,
        )

    except OSError as exc:
        if temporary_path.exists():
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

    return result