from decimal import Decimal

from app.domain.models.base_product import BaseProduct


class SerializedProduct(BaseProduct):
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

        self.serial_tracking = True