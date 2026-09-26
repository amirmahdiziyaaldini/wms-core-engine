import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from app.serialization.serializer import (
    serialize_entity,
    serialize_value,
    to_json,
)


class StatusEnum(Enum):
    ACTIVE = "active"


class SampleEntity:
    def __init__(self):
        self.name = "Test"
        self.price = Decimal("125.50")
        self.created_at = datetime(2026, 9, 26, 12, 30, 45)
        self.expiry_date = date(2026, 12, 31)
        self.status = StatusEnum.ACTIVE


def test_serialize_decimal_as_string():
    result = serialize_value(Decimal("125.50"))

    assert result == "125.50"
    assert isinstance(result, str)


def test_serialize_datetime_as_iso_string():
    value = datetime(2026, 9, 26, 12, 30, 45)

    result = serialize_value(value)

    assert result == "2026-09-26T12:30:45"


def test_serialize_date_as_iso_string():
    value = date(2026, 9, 26)

    result = serialize_value(value)

    assert result == "2026-09-26"


def test_serialize_enum_as_value():
    result = serialize_value(StatusEnum.ACTIVE)

    assert result == "active"


def test_serialize_list():
    result = serialize_value(
        [
            Decimal("10.50"),
            date(2026, 9, 26),
            StatusEnum.ACTIVE,
        ]
    )

    assert result == [
        "10.50",
        "2026-09-26",
        "active",
    ]


def test_serialize_dict():
    result = serialize_value(
        {
            "price": Decimal("50.00"),
            "status": StatusEnum.ACTIVE,
        }
    )

    assert result == {
        "price": "50.00",
        "status": "active",
    }


def test_serialize_entity():
    entity = SampleEntity()

    result = serialize_entity(entity)

    assert result["type"] == "SampleEntity"
    assert result["name"] == "Test"
    assert result["price"] == "125.50"
    assert result["created_at"] == "2026-09-26T12:30:45"
    assert result["expiry_date"] == "2026-12-31"
    assert result["status"] == "active"


def test_to_json_returns_valid_json():
    entity = SampleEntity()

    result = to_json(entity)

    data = json.loads(result)

    assert data["type"] == "SampleEntity"
    assert data["price"] == "125.50"
    assert data["status"] == "active"