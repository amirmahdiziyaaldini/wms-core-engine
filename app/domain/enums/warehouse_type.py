from enum import Enum


class WarehouseType(str, Enum):
    CENTRAL = "central"
    LOCAL = "local"
    SCRAP_QUARANTINE = "scrap_quarantine"