from decimal import Decimal


class BaseProduct:
    def __init__(
        self,
        sku: str,
        name: str,
        barcode: str,
        category: str,
        base_price: Decimal,
    ):
        if not isinstance(sku, str):
            raise ValueError("SKU must be a string")

        if not sku.strip():
            raise ValueError("SKU cannot be empty")

        if not isinstance(name, str):
            raise ValueError("Product name must be a string")

        if not name.strip():
            raise ValueError("Product name cannot be empty")

        if not isinstance(barcode, str):
            raise ValueError("Barcode must be a string")

        if not barcode.strip():
            raise ValueError("Barcode cannot be empty")

        if not isinstance(category, str):
            raise ValueError("Category must be a string")

        if not category.strip():
            raise ValueError("Category cannot be empty")

        if not isinstance(base_price, Decimal):
            raise ValueError("Base price must be a Decimal")

        if base_price < 0:
            raise ValueError("Base price cannot be negative")

        self.sku = sku
        self.name = name
        self.barcode = barcode
        self.category = category
        self.base_price = base_price
        self.expiry_tracking = False

    def get_price(self) -> Decimal:
        return self.base_price

    def to_dict(self) -> dict:
        return {
            "sku": self.sku,
            "name": self.name,
            "barcode": self.barcode,
            "category": self.category,
            "base_price": str(self.base_price),
        }