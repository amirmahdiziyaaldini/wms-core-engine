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