from decimal import Decimal

from app.domain.models.base_product import BaseProduct
from app.domain.models.bundle_component import BundleComponent


class BundleProduct(BaseProduct):
    def __init__(
        self,
        sku: str,
        name: str,
        barcode: str,
        category: str,
        base_price: Decimal,
        components: list[BundleComponent],
    ):
        if not isinstance(components, list):
            raise ValueError("Components must be a list")

        if not components:
            raise ValueError(
                "Bundle must contain at least one component"
            )

        for component in components:
            if not isinstance(component, BundleComponent):
                raise ValueError(
                    "All components must be BundleComponent instances"
                )

        super().__init__(
            sku=sku,
            name=name,
            barcode=barcode,
            category=category,
            base_price=base_price,
        )

        self.components = []

        for component in components:
            self.add_component(
                component.product,
                component.required_quantity,
            )

    def add_component(
        self,
        product: BaseProduct,
        required_quantity: int,
    ):
        component = BundleComponent(
            product=product,
            required_quantity=required_quantity,
        )

        if product is self:
            raise ValueError(
                "A BundleProduct cannot contain itself"
            )

        if isinstance(product, BundleProduct):
            if product._contains_product(self):
                raise ValueError(
                    "Circular Bundle reference detected"
                )

        self.components.append(component)

    def _contains_product(self, target: BaseProduct) -> bool:
        if self is target:
            return True

        for component in self.components:
            product = component.product

            if product is target:
                return True

            if isinstance(product, BundleProduct):
                if product._contains_product(target):
                    return True

        return False

    def get_sellable_quantity(
        self,
        available_stock: dict[str, int],
    ) -> int:
        sellable_quantities = []

        for component in self.components:
            product = component.product
            required_quantity = component.required_quantity

            if isinstance(product, BundleProduct):
                available_quantity = product.get_sellable_quantity(
                    available_stock
                )
            else:
                available_quantity = available_stock.get(
                    product.sku,
                    0,
                )

            sellable_quantity = (
                available_quantity // required_quantity
            )

            sellable_quantities.append(sellable_quantity)

        return min(sellable_quantities)

    def to_dict(self) -> dict:
        return {
            "sku": self.sku,
            "name": self.name,
            "barcode": self.barcode,
            "category": self.category,
            "base_price": str(self.base_price),
            "components": [
                {
                    "product_sku": component.product.sku,
                    "required_quantity": component.required_quantity,
                }
                for component in self.components
            ],
        }