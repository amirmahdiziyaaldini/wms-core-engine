from enum import Enum


class QCResult(Enum):
    APPROVED = "approved"
    INHERENT_DEFECT = "inherent_defect"
    REJECTED = "rejected"