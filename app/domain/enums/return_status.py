from enum import Enum


class ReturnStatus(Enum):
    REQUESTED = "requested"
    RECEIVED_AT_WAREHOUSE = "received_at_warehouse"
    QC_INSPECTION = "qc_inspection"
    APPROVED = "approved"
    REJECTED = "rejected"
    REFUNDED = "refunded"