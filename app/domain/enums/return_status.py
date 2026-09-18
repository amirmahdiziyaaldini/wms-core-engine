from enum import Enum


class ReturnStatus(Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    RECEIVED = "received"
    COMPLETED = "completed"