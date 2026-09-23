from app.domain.models.batch import Batch
from app.domain.models.warehouse import Warehouse


class Inventory:
    def __init__(self, warehouse: Warehouse):
        if not isinstance(warehouse, Warehouse):
            raise ValueError(
                "Warehouse must be a Warehouse"
            )

        self.warehouse = warehouse
        self.batches: list[Batch] = []

    def add_batch(self, batch: Batch):
        if not isinstance(batch, Batch):
            raise ValueError(
                "Batch must be a Batch"
            )

        self.batches.append(batch)