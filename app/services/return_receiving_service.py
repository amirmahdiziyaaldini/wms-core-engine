from datetime import datetime

from app.domain.enums.return_status import ReturnStatus
from app.domain.models.return_receipt import ReturnReceipt
from app.domain.models.return_request import ReturnRequest
from app.domain.models.shipment import Shipment
from app.domain.states.return_state_machine import ReturnStateMachine
from app.repositories.shipment_repository import ShipmentRepository


class ReturnReceivingService:

    def __init__(
        self,
        shipment_repository: ShipmentRepository | None = None,
    ):
        if shipment_repository is not None and not isinstance(
            shipment_repository,
            ShipmentRepository,
        ):
            raise ValueError(
                "Shipment repository must be a ShipmentRepository"
            )

        self.shipment_repository = (
            shipment_repository
            if shipment_repository is not None
            else ShipmentRepository()
        )

        self.return_state_machine = ReturnStateMachine()

    def receive(
        self,
        return_request: ReturnRequest,
        sku: str,
        quantity: int,
        serial_numbers: list[str] | None = None,
        receipt_id: str | None = None,
        received_at: datetime | None = None,
    ) -> ReturnReceipt:
        if not isinstance(return_request, ReturnRequest):
            raise ValueError(
                "Return request must be a ReturnRequest"
            )

        if not isinstance(sku, str):
            raise ValueError("SKU must be a string")

        if not sku.strip():
            raise ValueError("SKU cannot be empty")

        if isinstance(quantity, bool) or not isinstance(quantity, int):
            raise ValueError("Quantity must be an integer")

        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        if receipt_id is None:
            receipt_id = (
                f"RECEIPT-{return_request.return_id}-{sku}"
            )

        if not isinstance(receipt_id, str):
            raise ValueError("Receipt ID must be a string")

        if not receipt_id.strip():
            raise ValueError("Receipt ID cannot be empty")

        if received_at is not None and not isinstance(
            received_at,
            datetime,
        ):
            raise ValueError(
                "Received at must be a datetime"
            )

        if return_request.status not in {
            ReturnStatus.REQUESTED,
            ReturnStatus.RECEIVED_AT_WAREHOUSE,
        }:
            raise ValueError(
                "Return request cannot receive items in its current state"
            )

        received_quantities = getattr(return_request, "_received_quantities", {})
        received_receipt_ids = getattr(return_request, "_received_receipt_ids", [])
        received_serial_numbers = getattr(return_request, "_received_serial_numbers", {})

        if receipt_id in received_receipt_ids:
            raise ValueError("Receipt ID already exists for this return")

        requested_quantity = 0
        requested_serial_numbers: set[str] = set()

        for item in return_request.items:
            if item.sku != sku:
                continue

            requested_quantity += item.quantity

            if item.serial_numbers is not None:
                requested_serial_numbers.update(
                    item.serial_numbers
                )

        if requested_quantity == 0:
            raise ValueError(
                f"SKU {sku} is not part of the return request"
            )

        already_received_quantity = received_quantities.get(sku, 0)

        if already_received_quantity + quantity > requested_quantity:
            raise ValueError(
                "Received quantity cannot exceed requested quantity cumulatively"
            )

        if serial_numbers is not None:
            if len(serial_numbers) != quantity:
                raise ValueError(
                    "Number of serial numbers must match quantity"
                )

            shipment_serial_numbers = set()

            shipments = self.shipment_repository.get_by_order_id(
                return_request.order_id
            )

            for shipment in shipments:
                if not isinstance(shipment, Shipment):
                    continue

                shipment_serial_numbers.update(
                    shipment.serial_numbers
                )

            previously_received_serials = set(received_serial_numbers.get(sku, []))

            for serial_number in serial_numbers:
                if serial_number in previously_received_serials:
                    raise ValueError(
                        f"Serial number {serial_number} was already received for this return"
                    )

                if serial_number not in shipment_serial_numbers:
                    raise ValueError(
                        f"Serial number {serial_number} was not sold in the original order"
                    )

                if (
                    requested_serial_numbers
                    and serial_number not in requested_serial_numbers
                ):
                    raise ValueError(
                        f"Serial number {serial_number} is not part of the return request"
                    )

        receipt = ReturnReceipt(
            receipt_id=receipt_id,
            return_id=return_request.return_id,
            sku=sku,
            quantity=quantity,
            serial_numbers=serial_numbers,
            location="RETURN_QUARANTINE",
            status=ReturnStatus.RECEIVED_AT_WAREHOUSE.value,
            received_at=received_at,
        )

        if return_request.status == ReturnStatus.REQUESTED:
            self.return_state_machine.transition(
                return_request,
                ReturnStatus.RECEIVED_AT_WAREHOUSE,
                timestamp=receipt.received_at,
            )

        received_quantities[sku] = already_received_quantity + quantity
        received_receipt_ids.append(receipt_id)

        if serial_numbers is not None:
            received_serial_numbers.setdefault(sku, []).extend(serial_numbers)

        return_request._received_quantities = received_quantities
        return_request._received_receipt_ids = received_receipt_ids
        return_request._received_serial_numbers = received_serial_numbers

        return receipt