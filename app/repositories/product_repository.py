from app.domain.models.base_product import BaseProduct


class ProductRepository:

    def __init__(self):
        self._products: dict[str, BaseProduct] = {}

    def save(self, product: BaseProduct) -> None:
        if not isinstance(product, BaseProduct):
            raise ValueError(
                "Product must be a BaseProduct"
            )

        if product.sku in self._products:
            raise ValueError(
                f"Product already exists: {product.sku}"
            )

        self._products[product.sku] = product

    def get(self, sku: str) -> BaseProduct | None:
        if not isinstance(sku, str):
            raise ValueError(
                "SKU must be a string"
            )

        return self._products.get(sku)

    def list_all(self) -> list[BaseProduct]:
        return list(self._products.values())

    def delete(self, sku: str) -> None:
        if not isinstance(sku, str):
            raise ValueError(
                "SKU must be a string"
            )

        self._products.pop(sku, None)

    def exists(self, sku: str) -> bool:
        if not isinstance(sku, str):
            raise ValueError(
                "SKU must be a string"
            )

        return sku in self._products