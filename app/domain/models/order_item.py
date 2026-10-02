from decimal import Decimal


class OrderItem:

    def __init__(
        self,
        item_id: str,
        sku: str,
        quantity: int,
        product_name: str | None = None,
        unit_price: Decimal | None = None,
        discount: Decimal = Decimal("0"),
    ):
        if not isinstance(item_id, str):
            raise ValueError("Item ID must be a string")

        if not item_id.strip():
            raise ValueError("Item ID cannot be empty")

        if not isinstance(sku, str):
            raise ValueError("SKU must be a string")

        if not sku.strip():
            raise ValueError("SKU cannot be empty")

        if isinstance(quantity, bool) or not isinstance(quantity, int):
            raise ValueError("Quantity must be an integer")

        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        if product_name is not None:
            if not isinstance(product_name, str):
                raise ValueError(
                    "Product name must be a string"
                )

            if not product_name.strip():
                raise ValueError(
                    "Product name cannot be empty"
                )

        if unit_price is not None:
            if not isinstance(unit_price, Decimal):
                raise ValueError(
                    "Unit price must be a Decimal"
                )

            if unit_price < Decimal("0"):
                raise ValueError(
                    "Unit price cannot be negative"
                )

        if not isinstance(discount, Decimal):
            raise ValueError(
                "Discount must be a Decimal"
            )

        if discount < Decimal("0"):
            raise ValueError(
                "Discount cannot be negative"
            )

        if unit_price is not None:
            gross_total = unit_price * quantity

            if discount > gross_total:
                raise ValueError(
                    "Discount cannot exceed gross total"
                )

        self.item_id = item_id
        self.sku = sku
        self._quantity = quantity
        self.product_name = product_name
        self._unit_price = unit_price
        self._discount = discount
        self._line_total = self._calculate_line_total()

    @property
    def quantity(self) -> int:
        return self._quantity

    @quantity.setter
    def quantity(self, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("Quantity must be an integer")

        if value <= 0:
            raise ValueError("Quantity must be positive")

        unit_price = getattr(self, "_unit_price", None)
        discount = getattr(self, "_discount", Decimal("0"))

        if unit_price is not None:
            gross_total = unit_price * value
            if discount > gross_total:
                raise ValueError("Discount cannot exceed gross total")

        self._quantity = value
        self._line_total = self._calculate_line_total()

    @property
    def unit_price(self) -> Decimal | None:
        return self._unit_price

    @property
    def discount(self) -> Decimal:
        return self._discount

    @property
    def line_total(self) -> Decimal | None:
        return self._calculate_line_total()

    def _calculate_line_total(self) -> Decimal | None:
        unit_price = getattr(self, "_unit_price", None)
        discount = getattr(self, "_discount", Decimal("0"))

        if unit_price is None:
            return None

        return (
            unit_price * self.quantity
        ) - discount

    def set_price_snapshot(
        self,
        unit_price: Decimal,
        product_name: str | None = None,
        discount: Decimal = Decimal("0"),
    ) -> None:
        if not isinstance(unit_price, Decimal):
            raise ValueError(
                "Unit price must be a Decimal"
            )

        if unit_price < Decimal("0"):
            raise ValueError(
                "Unit price cannot be negative"
            )

        if product_name is not None:
            if not isinstance(product_name, str):
                raise ValueError(
                    "Product name must be a string"
                )

            if not product_name.strip():
                raise ValueError(
                    "Product name cannot be empty"
                )

        if not isinstance(discount, Decimal):
            raise ValueError(
                "Discount must be a Decimal"
            )

        if discount < Decimal("0"):
            raise ValueError(
                "Discount cannot be negative"
            )

        gross_total = unit_price * self.quantity

        if discount > gross_total:
            raise ValueError(
                "Discount cannot exceed gross total"
            )

        if product_name is not None:
            self.product_name = product_name

        self._unit_price = unit_price
        self._discount = discount
        self._line_total = gross_total - discount

    def set_unit_price(
        self,
        unit_price: Decimal,
    ) -> None:
        self.set_price_snapshot(
            unit_price=unit_price,
            discount=self._discount,
        )

    def get_line_total(self) -> Decimal:
        if self._line_total is None:
            raise ValueError(
                "Line total is not available before price snapshot"
            )

        return self._line_total