from collections.abc import Iterable

from app.domain.models.sales_rule_context import SalesRuleContext
from app.strategies.sales_rules.sales_rule import SalesRule


class SalesRuleEngine:
    def __init__(
        self,
        rules: Iterable[SalesRule] | None = None,
    ):
        self.rules: list[SalesRule] = []

        if rules is not None:
            for rule in rules:
                self.add_rule(rule)

    def add_rule(self, rule: SalesRule) -> None:
        if not isinstance(rule, SalesRule):
            raise ValueError("Rule must be a SalesRule")

        self.rules.append(rule)

    def validate(self, context: SalesRuleContext) -> None:
        if not isinstance(context, SalesRuleContext):
            raise ValueError(
                "Context must be a SalesRuleContext"
            )

        for rule in self.rules:
            rule.validate(context)