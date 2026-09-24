from enum import Enum

class InventoryTransactionType(Enum):
    RECEIPT = "receipt"
    SALE = "sale"
    TRANSFER = "transfer"
    RETURN = "return"

    RECEIVE = "receive"
    RESERVE = "reserve"
    RELEASE_RESERVATION = "release_reservation"
    SHIP = "ship"
    ISSUE = "issue"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    RETURN_TO_STOCK = "return_to_stock"
    SCRAP = "scrap"