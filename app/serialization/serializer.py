import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any


REFERENCE_FIELDS = {
    "product": "sku",
    "parent_product": "sku",
    "warehouse": "warehouse_id",
    "source": "warehouse_id",
    "destination": "warehouse_id",
    "order": "order_id",
    "inventory": "warehouse_id",
}


def serialize_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, list):
        return [
            serialize_value(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            serialize_value(item)
            for item in value
        ]

    if isinstance(value, dict):
        return {
            str(key): serialize_value(item)
            for key, item in value.items()
        }

    if hasattr(value, "to_dict") and callable(value.to_dict):
        return serialize_value(
            value.to_dict()
        )

    if hasattr(value, "__dict__"):
        return serialize_entity(
            value
        )

    return value


def _get_reference_value(
    value: Any,
    field_name: str,
) -> Any:

    reference_attribute = REFERENCE_FIELDS.get(
        field_name
    )

    if reference_attribute is None:
        return None

    reference_value = getattr(
        value,
        reference_attribute,
        None,
    )

    if reference_value is None:
        return None

    return serialize_value(
        reference_value
    )


def serialize_entity(
    entity: Any,
) -> dict[str, Any]:

    if entity is None:
        return {}

    if not hasattr(
        entity,
        "__dict__",
    ):
        raise TypeError(
            "Entity must be an object"
        )

    data = {
        "type": entity.__class__.__name__,
    }

    for field_name, field_value in vars(
        entity
    ).items():

        if field_name.startswith("_"):
            public_name = field_name[1:]
        else:
            public_name = field_name

        if field_name == "type":
            public_name = "transaction_type"

        reference_value = _get_reference_value(
            field_value,
            field_name,
        )

        if reference_value is not None:
            data[public_name] = reference_value
            continue

        data[public_name] = serialize_value(
            field_value
        )

    return data


def to_json(
    entity: Any,
) -> str:

    return json.dumps(
        serialize_entity(entity),
        ensure_ascii=False,
        indent=4,
    )