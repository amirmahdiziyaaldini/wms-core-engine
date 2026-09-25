from decimal import Decimal

class OrderItem:

    def __init__(
        self,
        item_id: str,
        sku: str,
        quantity: int,
    ):
        if not isinstance(item_id, str):
            raise ValueError(
                "Item ID must be a string"
            )

        if not item_id.strip():
            raise ValueError(
                "Item ID cannot be empty"
            )

        if not isinstance(sku, str):
            raise ValueError(
                "SKU must be a string"
            )

        if not sku.strip():
            raise ValueError(
                "SKU cannot be empty"
            )

        if not isinstance(quantity, int) or isinstance(
            quantity,
            bool,
        ):
            raise ValueError(
                "Quantity must be an integer"
            )

        if quantity <= 0:
            raise ValueError(
                "Quantity must be greater than zero"
            )

        self.item_id = item_id
        self.sku = sku
        self.quantity = quantity
        self.unit_price: Decimal | None = None
        self.line_total: Decimal | None = None

    def set_unit_price(
        self,
        unit_price: Decimal,
    ) -> None:
        if not isinstance(unit_price, Decimal):
            raise ValueError(
                "Unit price must be a Decimal"
            )

        if unit_price < Decimal("0"):
            raise ValueError(
                "Unit price cannot be negative"
            )

        self.unit_price = unit_price
        self.line_total = (
            unit_price * Decimal(self.quantity)
        )

    def get_line_total(self) -> Decimal:
        if self.line_total is None:
            raise ValueError(
                "Price snapshot has not been created"
            )

        return self.line_total