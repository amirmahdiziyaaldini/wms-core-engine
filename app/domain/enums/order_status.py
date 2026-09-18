from enum import Enum

class OrderStatus(Enum):
    CREATED = "created"
    RESERVED = "reserved"
    PAID = "paid"
    SHIPPED = "shipped"
    COMPLETED = "completed"