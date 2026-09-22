from decimal import Decimal

from app.domain.models.base_product import BaseProduct


class PerishableProduct(BaseProduct):
    def __init__(
        self,
        sku: str,
        name: str,
        barcode: str,
        category: str,
        base_price: Decimal,
    ):
        super().__init__(
            sku=sku,
            name=name,
            barcode=barcode,
            category=category,
            base_price=base_price,
        )

        self.expiry_tracking = True

    def get_price(self) -> Decimal:
        return self.base_price