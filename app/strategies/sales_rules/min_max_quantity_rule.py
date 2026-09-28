from collections import defaultdict
from collections.abc import Mapping

from app.domain.models.sales_rule_context import SalesRuleContext
from app.strategies.sales_rules.sales_rule import SalesRule


class MinMaxQuantityRule(SalesRule):
    def __init__(
        self,
        limits: Mapping[str, tuple[int | None, int | None]],
    ):
        if not isinstance(limits, Mapping):
            raise ValueError(
                "Limits must be a mapping"
            )

        if not limits:
            raise ValueError(
                "At least one quantity limit is required"
            )

        self.limits: dict[
            str,
            tuple[int | None, int | None],
        ] = {}

        for sku, limit in limits.items():
            if not isinstance(sku, str):
                raise ValueError(
                    "SKU must be a string"
                )

            if not sku.strip():
                raise ValueError(
                    "SKU cannot be empty"
                )

            if (
                not isinstance(limit, tuple)
                or len(limit) != 2
            ):
                raise ValueError(
                    "Quantity limit must be a tuple of "
                    "(min_quantity, max_quantity)"
                )

            min_quantity, max_quantity = limit

            if min_quantity is not None:
                if (
                    not isinstance(min_quantity, int)
                    or isinstance(min_quantity, bool)
                ):
                    raise ValueError(
                        "Minimum quantity must be an integer"
                    )

                if min_quantity <= 0:
                    raise ValueError(
                        "Minimum quantity must be positive"
                    )

            if max_quantity is not None:
                if (
                    not isinstance(max_quantity, int)
                    or isinstance(max_quantity, bool)
                ):
                    raise ValueError(
                        "Maximum quantity must be an integer"
                    )

                if max_quantity <= 0:
                    raise ValueError(
                        "Maximum quantity must be positive"
                    )

            if (
                min_quantity is not None
                and max_quantity is not None
                and max_quantity < min_quantity
            ):
                raise ValueError(
                    "Maximum quantity cannot be lower "
                    "than minimum quantity"
                )

            if (
                min_quantity is None
                and max_quantity is None
            ):
                raise ValueError(
                    "At least one quantity limit is required"
                )

            self.limits[sku] = (
                min_quantity,
                max_quantity,
            )

    def validate(
        self,
        context: SalesRuleContext,
    ) -> None:
        if not isinstance(
            context,
            SalesRuleContext,
        ):
            raise ValueError(
                "Context must be a SalesRuleContext"
            )

        quantities = defaultdict(int)

        for item in context.order.items:
            quantities[item.sku] += item.quantity

        for sku, quantity in quantities.items():
            limit = self.limits.get(sku)

            if limit is None:
                continue

            min_quantity, max_quantity = limit

            if (
                min_quantity is not None
                and quantity < min_quantity
            ):
                raise ValueError(
                    f"Minimum quantity for SKU "
                    f"{sku} is {min_quantity}"
                )

            if (
                max_quantity is not None
                and quantity > max_quantity
            ):
                raise ValueError(
                    f"Maximum quantity for SKU "
                    f"{sku} is {max_quantity}"
                )