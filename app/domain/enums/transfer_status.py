from enum import Enum


class TransferStatus(str, Enum):
    CREATED = "created"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    COMPLETED = "completed"
    CANCELLED = "cancelled"