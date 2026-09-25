from abc import ABC, abstractmethod
from decimal import Decimal

from app.domain.models.base_product import BaseProduct


class PricingStrategy(ABC):
    @abstractmethod
    def calculate_unit_price(
        self,
        product: BaseProduct,
        quantity: int,
    ) -> Decimal:
        raise NotImplementedError