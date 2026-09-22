from app.domain.models.base_product import BaseProduct


class BundleComponent:
    def __init__(
        self,
        product: BaseProduct,
        required_quantity: int,
    ):
        if not isinstance(product, BaseProduct):
            raise ValueError(
                "Product must be a BaseProduct"
            )

        if not isinstance(required_quantity, int):
            raise ValueError(
                "Required quantity must be an integer"
            )

        if required_quantity <= 0:
            raise ValueError(
                "Required quantity must be greater than zero"
            )

        self.product = product
        self.required_quantity = required_quantity