from enum import Enum

class InventoryTransactionType(Enum):
    RECEIPT = "receipt"
    SALE = "sale"
    TRANSFER = "transfer"
    RETURN = "return"