from dataclasses import dataclass
from decimal import Decimal
from collections.abc import Iterable

from app.domain.models.base_product import BaseProduct
from app.strategies.pricing.pricing_strategy import PricingStrategy


@dataclass(frozen=True)
class PriceTier:
    min_quantity: int
    max_quantity: int | None
    discount_rate: Decimal


class TieredPricingStrategy(PricingStrategy):
    def __init__(
        self,
        tiers: Iterable[PriceTier] | None = None,
    ):
        if tiers is None:
            tiers = [
                PriceTier(
                    min_quantity=1,
                    max_quantity=5,
                    discount_rate=Decimal("0"),
                ),
                PriceTier(
                    min_quantity=6,
                    max_quantity=20,
                    discount_rate=Decimal("0.10"),
                ),
                PriceTier(
                    min_quantity=21,
                    max_quantity=None,
                    discount_rate=Decimal("0.20"),
                ),
            ]

        self.tiers = list(tiers)
        self._validate_tiers()

    def _validate_tiers(self) -> None:
        if not self.tiers:
            raise ValueError("At least one price tier is required")

        for index, tier in enumerate(self.tiers):
            if not isinstance(tier.min_quantity, int):
                raise ValueError(
                    "Tier minimum quantity must be an integer"
                )

            if isinstance(tier.min_quantity, bool):
                raise ValueError(
                    "Tier minimum quantity must be an integer"
                )

            if tier.min_quantity < 1:
                raise ValueError(
                    "Tier minimum quantity must be positive"
                )

            if tier.max_quantity is not None:
                if not isinstance(tier.max_quantity, int):
                    raise ValueError(
                        "Tier maximum quantity must be an integer"
                    )

                if isinstance(tier.max_quantity, bool):
                    raise ValueError(
                        "Tier maximum quantity must be an integer"
                    )

                if tier.max_quantity < tier.min_quantity:
                    raise ValueError(
                        "Tier maximum quantity cannot be lower than minimum quantity"
                    )

            if not isinstance(tier.discount_rate, Decimal):
                raise ValueError(
                    "Tier discount rate must be a Decimal"
                )

            if tier.discount_rate < Decimal("0"):
                raise ValueError(
                    "Tier discount rate cannot be negative"
                )

            if tier.discount_rate > Decimal("1"):
                raise ValueError(
                    "Tier discount rate cannot exceed 1"
                )

            if index == 0 and tier.min_quantity != 1:
                raise ValueError(
                    "The first tier must start at quantity 1"
                )

            if index > 0:
                previous = self.tiers[index - 1]

                if previous.max_quantity is None:
                    raise ValueError(
                        "An open-ended tier must be the last tier"
                    )

                expected_min = previous.max_quantity + 1

                if tier.min_quantity != expected_min:
                    raise ValueError(
                        "Price tiers must not contain gaps or overlaps"
                    )

        if (
            self.tiers[-1].max_quantity is not None
            and self.tiers[-1].max_quantity < self.tiers[-1].min_quantity
        ):
            raise ValueError(
                "Invalid final price tier"
            )

    def _find_tier(self, quantity: int) -> PriceTier:
        for tier in self.tiers:
            if quantity < tier.min_quantity:
                continue

            if (
                tier.max_quantity is None
                or quantity <= tier.max_quantity
            ):
                return tier

        raise ValueError(
            f"No price tier found for quantity {quantity}"
        )

    def calculate_unit_price(
        self,
        product: BaseProduct,
        quantity: int,
    ) -> Decimal:
        if not isinstance(product, BaseProduct):
            raise ValueError(
                "Product must be a BaseProduct"
            )

        if not isinstance(quantity, int) or isinstance(quantity, bool):
            raise ValueError(
                "Quantity must be an integer"
            )

        if quantity <= 0:
            raise ValueError(
                "Quantity must be positive"
            )

        base_price = product.get_price()

        if not isinstance(base_price, Decimal):
            raise ValueError(
                "Product price must be a Decimal"
            )

        tier = self._find_tier(quantity)

        return base_price * (
            Decimal("1") - tier.discount_rate
        )