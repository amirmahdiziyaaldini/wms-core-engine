import pytest

from app.domain.enums.warehouse_type import WarehouseType
from app.domain.models.warehouse import Warehouse


def create_warehouse():
    return Warehouse(
        warehouse_id="WH-001",
        name="Central Warehouse",
        location="Tehran",
        warehouse_type=WarehouseType.CENTRAL,
    )


def test_create_warehouse():
    warehouse = create_warehouse()

    assert warehouse.warehouse_id == "WH-001"
    assert warehouse.name == "Central Warehouse"
    assert warehouse.location == "Tehran"
    assert warehouse.warehouse_type == WarehouseType.CENTRAL


def test_warehouse_keeps_warehouse_id():
    warehouse = create_warehouse()

    assert warehouse.warehouse_id == "WH-001"


def test_warehouse_keeps_name():
    warehouse = create_warehouse()

    assert warehouse.name == "Central Warehouse"


def test_warehouse_keeps_location():
    warehouse = create_warehouse()

    assert warehouse.location == "Tehran"


def test_create_central_warehouse():
    warehouse = Warehouse(
        warehouse_id="WH-CENTRAL-001",
        name="Central Warehouse",
        location="Tehran",
        warehouse_type=WarehouseType.CENTRAL,
    )

    assert warehouse.warehouse_type == WarehouseType.CENTRAL


def test_create_local_warehouse():
    warehouse = Warehouse(
        warehouse_id="WH-LOCAL-001",
        name="Local Warehouse",
        location="Shiraz",
        warehouse_type=WarehouseType.LOCAL,
    )

    assert warehouse.warehouse_type == WarehouseType.LOCAL


def test_create_scrap_quarantine_warehouse():
    warehouse = Warehouse(
        warehouse_id="WH-SCRAP-001",
        name="Scrap Quarantine Warehouse",
        location="Tehran",
        warehouse_type=WarehouseType.SCRAP_QUARANTINE,
    )

    assert (
        warehouse.warehouse_type
        == WarehouseType.SCRAP_QUARANTINE
    )


def test_warehouse_id_must_be_string():
    with pytest.raises(
        ValueError,
        match="Warehouse ID must be a string",
    ):
        Warehouse(
            warehouse_id=1001,
            name="Central Warehouse",
            location="Tehran",
            warehouse_type=WarehouseType.CENTRAL,
        )


def test_warehouse_id_cannot_be_empty():
    with pytest.raises(
        ValueError,
        match="Warehouse ID cannot be empty",
    ):
        Warehouse(
            warehouse_id="",
            name="Central Warehouse",
            location="Tehran",
            warehouse_type=WarehouseType.CENTRAL,
        )


def test_warehouse_id_cannot_contain_only_whitespace():
    with pytest.raises(
        ValueError,
        match="Warehouse ID cannot be empty",
    ):
        Warehouse(
            warehouse_id="   ",
            name="Central Warehouse",
            location="Tehran",
            warehouse_type=WarehouseType.CENTRAL,
        )


def test_warehouse_name_must_be_string():
    with pytest.raises(
        ValueError,
        match="Warehouse name must be a string",
    ):
        Warehouse(
            warehouse_id="WH-001",
            name=1001,
            location="Tehran",
            warehouse_type=WarehouseType.CENTRAL,
        )


def test_warehouse_name_cannot_be_empty():
    with pytest.raises(
        ValueError,
        match="Warehouse name cannot be empty",
    ):
        Warehouse(
            warehouse_id="WH-001",
            name="",
            location="Tehran",
            warehouse_type=WarehouseType.CENTRAL,
        )


def test_warehouse_name_cannot_contain_only_whitespace():
    with pytest.raises(
        ValueError,
        match="Warehouse name cannot be empty",
    ):
        Warehouse(
            warehouse_id="WH-001",
            name="   ",
            location="Tehran",
            warehouse_type=WarehouseType.CENTRAL,
        )


def test_warehouse_location_must_be_string():
    with pytest.raises(
        ValueError,
        match="Warehouse location must be a string",
    ):
        Warehouse(
            warehouse_id="WH-001",
            name="Central Warehouse",
            location=1001,
            warehouse_type=WarehouseType.CENTRAL,
        )


def test_warehouse_location_cannot_be_empty():
    with pytest.raises(
        ValueError,
        match="Warehouse location cannot be empty",
    ):
        Warehouse(
            warehouse_id="WH-001",
            name="Central Warehouse",
            location="",
            warehouse_type=WarehouseType.CENTRAL,
        )


def test_warehouse_location_cannot_contain_only_whitespace():
    with pytest.raises(
        ValueError,
        match="Warehouse location cannot be empty",
    ):
        Warehouse(
            warehouse_id="WH-001",
            name="Central Warehouse",
            location="   ",
            warehouse_type=WarehouseType.CENTRAL,
        )


def test_warehouse_type_must_be_warehouse_type():
    with pytest.raises(
        ValueError,
        match="Warehouse type must be a WarehouseType",
    ):
        Warehouse(
            warehouse_id="WH-001",
            name="Central Warehouse",
            location="Tehran",
            warehouse_type="central",
        )


def test_warehouse_does_not_execute_order_or_rma_operations():
    warehouse = create_warehouse()

    assert not hasattr(warehouse, "create_order")
    assert not hasattr(warehouse, "reserve_order")
    assert not hasattr(warehouse, "approve_rma")
    assert not hasattr(warehouse, "refund")