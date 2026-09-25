from collections.abc import Mapping

from app.domain.models.base_product import BaseProduct
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.strategies.pricing.pricing_strategy import PricingStrategy
from app.strategies.pricing.tiered_pricing_strategy import (
    TieredPricingStrategy,
)


class PricingService:
    def __init__(
        self,
        pricing_strategy: PricingStrategy | None = None,
    ):
        self.pricing_strategy = (
            pricing_strategy
            if pricing_strategy is not None
            else TieredPricingStrategy()
        )

    def price_item(
        self,
        item: OrderItem,
        product: BaseProduct,
    ) -> None:
        if not isinstance(item, OrderItem):
            raise ValueError(
                "Item must be an OrderItem"
            )

        if not isinstance(product, BaseProduct):
            raise ValueError(
                "Product must be a BaseProduct"
            )

        if item.sku != product.sku:
            raise ValueError(
                "Order item SKU does not match product SKU"
            )

        unit_price = self.pricing_strategy.calculate_unit_price(
            product=product,
            quantity=item.quantity,
        )

        item.set_unit_price(unit_price)

    def price_order(
        self,
        order: Order,
        products_by_sku: Mapping[str, BaseProduct],
    ) -> None:
        if not isinstance(order, Order):
            raise ValueError(
                "Order must be an Order"
            )

        if not isinstance(products_by_sku, Mapping):
            raise ValueError(
                "Products must be a mapping"
            )

        calculated_prices = []

        for item in order.items:
            product = products_by_sku.get(item.sku)

            if product is None:
                raise ValueError(
                    f"Product not found for SKU {item.sku}"
                )

            unit_price = self.pricing_strategy.calculate_unit_price(
                product=product,
                quantity=item.quantity,
            )

            calculated_prices.append(
                (item, unit_price)
            )

        for item, unit_price in calculated_prices:
            item.set_unit_price(unit_price)