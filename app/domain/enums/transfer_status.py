from enum import Enum

class TransferStatus(Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    COMPLETED = "completed"