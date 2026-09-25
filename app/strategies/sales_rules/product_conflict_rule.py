from collections.abc import Iterable

from app.domain.models.sales_rule_context import SalesRuleContext
from app.strategies.sales_rules.sales_rule import SalesRule


class ProductConflictRule(SalesRule):
    def __init__(
        self,
        conflicts: Iterable[Iterable[str]],
    ):
        self.conflicts: list[frozenset[str]] = []

        for conflict in conflicts:
            conflict_set = frozenset(conflict)

            if len(conflict_set) < 2:
                raise ValueError(
                    "Each conflict must contain at least two SKUs"
                )

            for sku in conflict_set:
                if not isinstance(sku, str):
                    raise ValueError(
                        "Conflict SKU must be a string"
                    )

                if not sku.strip():
                    raise ValueError(
                        "Conflict SKU cannot be empty"
                    )

            if conflict_set not in self.conflicts:
                self.conflicts.append(conflict_set)

    def validate(
        self,
        context: SalesRuleContext,
    ) -> None:
        order_skus = {
            item.sku
            for item in context.order.items
        }

        for conflict in self.conflicts:
            if conflict.issubset(order_skus):
                conflicting_skus = ", ".join(
                    sorted(conflict)
                )

                raise ValueError(
                    f"Conflicting SKUs in order: "
                    f"{conflicting_skus}"
                )