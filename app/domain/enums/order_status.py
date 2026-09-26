from enum import Enum

class OrderStatus(Enum):
    CREATED = "created"
    RESERVED = "reserved"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"