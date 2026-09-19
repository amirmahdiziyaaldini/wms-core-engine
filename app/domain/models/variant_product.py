from decimal import Decimal

from app.domain.models.base_product import BaseProduct


class VariantProduct(BaseProduct):
    def __init__(
        self,
        sku: str,
        name: str,
        barcode: str,
        category: str,
        attributes: dict,
        price_modifier: Decimal,
        parent_product: BaseProduct,
    ):
        if not isinstance(attributes, dict):
            raise ValueError("Attributes must be a dictionary")

        if not isinstance(price_modifier, Decimal):
            raise ValueError("Price modifier must be a Decimal")

        if not isinstance(parent_product, BaseProduct):
            raise ValueError("Parent product must be a BaseProduct")

        super().__init__(
            sku=sku,
            name=name,
            barcode=barcode,
            category=category,
            base_price=parent_product.base_price,
        )

        self.attributes = attributes
        self.price_modifier = price_modifier
        self.parent_product = parent_product

    def get_price(self) -> Decimal:
        final_price = self.base_price + self.price_modifier

        if final_price < 0:
            raise ValueError("Final price cannot be negative")

        return final_price

    def to_dict(self) -> dict:
        return {
            "sku": self.sku,
            "name": self.name,
            "barcode": self.barcode,
            "category": self.category,
            "base_price": str(self.base_price),
            "attributes": self.attributes,
            "price_modifier": str(self.price_modifier),
            "parent_product_sku": self.parent_product.sku,
        }