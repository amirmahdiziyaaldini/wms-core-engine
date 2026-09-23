class Reservation:
    def __init__(
        self,
        reservation_id: str,
        order_id: str,
        order_item_id: str,
        sku: str,
        quantity: int,
        batch_allocations: dict[str, int] | None = None,
    ):
        if not isinstance(reservation_id, str):
            raise ValueError(
                "Reservation ID must be a string"
            )

        if not reservation_id.strip():
            raise ValueError(
                "Reservation ID cannot be empty"
            )

        if not isinstance(order_id, str):
            raise ValueError(
                "Order ID must be a string"
            )

        if not order_id.strip():
            raise ValueError(
                "Order ID cannot be empty"
            )

        if not isinstance(order_item_id, str):
            raise ValueError(
                "Order item ID must be a string"
            )

        if not order_item_id.strip():
            raise ValueError(
                "Order item ID cannot be empty"
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

        if batch_allocations is not None:
            if not isinstance(batch_allocations, dict):
                raise ValueError(
                    "Batch allocations must be a dictionary"
                )

            total_allocated = 0

            for batch_id, allocated_quantity in batch_allocations.items():
                if not isinstance(batch_id, str):
                    raise ValueError(
                        "Batch ID must be a string"
                    )

                if not batch_id.strip():
                    raise ValueError(
                        "Batch ID cannot be empty"
                    )

                if not isinstance(
                    allocated_quantity,
                    int,
                ) or isinstance(
                    allocated_quantity,
                    bool,
                ):
                    raise ValueError(
                        "Allocated quantity must be an integer"
                    )

                if allocated_quantity <= 0:
                    raise ValueError(
                        "Allocated quantity must be greater than zero"
                    )

                total_allocated += allocated_quantity

            if total_allocated > quantity:
                raise ValueError(
                    "Total batch allocation cannot exceed reservation quantity"
                )

            batch_allocations = batch_allocations.copy()

        self.reservation_id = reservation_id
        self.order_id = order_id
        self.order_item_id = order_item_id
        self.sku = sku
        self.quantity = quantity
        self.batch_allocations = batch_allocations or {}