from app.domain.enums.warehouse_type import WarehouseType


class Warehouse:
    def __init__(
        self,
        warehouse_id: str,
        name: str,
        location: str,
        warehouse_type: WarehouseType,
    ):
        if not isinstance(warehouse_id, str):
            raise ValueError("Warehouse ID must be a string")

        if not warehouse_id.strip():
            raise ValueError("Warehouse ID cannot be empty")

        if not isinstance(name, str):
            raise ValueError("Warehouse name must be a string")

        if not name.strip():
            raise ValueError("Warehouse name cannot be empty")

        if not isinstance(location, str):
            raise ValueError("Warehouse location must be a string")

        if not location.strip():
            raise ValueError("Warehouse location cannot be empty")

        if not isinstance(warehouse_type, WarehouseType):
            raise ValueError(
                "Warehouse type must be a WarehouseType"
            )

        self.warehouse_id = warehouse_id
        self.name = name
        self.location = location
        self.warehouse_type = warehouse_type