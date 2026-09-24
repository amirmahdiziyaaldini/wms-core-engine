from abc import ABC, abstractmethod
from datetime import date

from app.domain.models.batch import Batch


class StockAllocationStrategy(ABC):
    @abstractmethod
    def allocate(
        self,
        batches: list[Batch],
        quantity: int,
        reference_date: date | None = None,
    ) -> dict[str, int]:
        pass