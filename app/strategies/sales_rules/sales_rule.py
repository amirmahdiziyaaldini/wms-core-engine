from abc import ABC, abstractmethod

from app.domain.models.sales_rule_context import SalesRuleContext


class SalesRule(ABC):
    @abstractmethod
    def validate(self, context: SalesRuleContext) -> None:
        raise NotImplementedError