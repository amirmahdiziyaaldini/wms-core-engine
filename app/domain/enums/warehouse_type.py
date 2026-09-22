from enum import Enum


class WarehouseType(Enum):
    CENTRAL = "central"
    LOCAL = "local"
    SCRAP_QUARANTINE = "scrap_quarantine"