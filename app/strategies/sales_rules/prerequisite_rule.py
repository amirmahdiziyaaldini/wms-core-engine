from collections.abc import Iterable

from app.domain.models.sales_rule_context import SalesRuleContext
from app.strategies.sales_rules.sales_rule import SalesRule


class PrerequisiteRule(SalesRule):
    def __init__(
        self,
        required_sku: str,
        child_skus: Iterable[str],
        mode: str = "any",
    ):
        if not isinstance(required_sku, str):
            raise ValueError("Required SKU must be a string")

        if not required_sku.strip():
            raise ValueError("Required SKU cannot be empty")

        if not isinstance(mode, str):
            raise ValueError("Mode must be a string")

        if mode not in {"any", "all"}:
            raise ValueError("Mode must be either 'any' or 'all'")

        self.required_sku = required_sku
        self.child_skus = list(child_skus)
        self.mode = mode

        if not self.child_skus:
            raise ValueError("At least one child SKU is required")

        normalized_child_skus = []

        for sku in self.child_skus:
            if not isinstance(sku, str):
                raise ValueError("Child SKU must be a string")

            if not sku.strip():
                raise ValueError("Child SKU cannot be empty")

            if sku not in normalized_child_skus:
                normalized_child_skus.append(sku)

        self.child_skus = normalized_child_skus

    def validate(
        self,
        context: SalesRuleContext,
    ) -> None:
        order_skus = {
            item.sku
            for item in context.order.items
        }

        if self.mode == "any":
            condition_met = any(
                sku in order_skus
                for sku in self.child_skus
            )
        else:
            condition_met = all(
                sku in order_skus
                for sku in self.child_skus
            )

        if not condition_met:
            return

        if self.required_sku not in order_skus:
            raise ValueError(
                f"Prerequisite SKU '{self.required_sku}' "
                f"is required when purchasing: "
                f"{', '.join(self.child_skus)}"
            )