from datetime import datetime

from app.domain.enums.return_status import ReturnStatus
from app.domain.exceptions.invalid_return_state import InvalidReturnStateError
from app.domain.models.return_request import ReturnRequest


class ReturnStateMachine:

    _TRANSITIONS = {
        ReturnStatus.REQUESTED: {
            ReturnStatus.RECEIVED_AT_WAREHOUSE,
            ReturnStatus.REJECTED,
        },
        ReturnStatus.RECEIVED_AT_WAREHOUSE: {
            ReturnStatus.QC_INSPECTION,
            ReturnStatus.REJECTED,
        },
        ReturnStatus.QC_INSPECTION: {
            ReturnStatus.APPROVED,
            ReturnStatus.REJECTED,
        },
        ReturnStatus.APPROVED: {
            ReturnStatus.REFUNDED,
        },
        ReturnStatus.REJECTED: set(),
        ReturnStatus.REFUNDED: set(),
    }

    def can_transition(
        self,
        current_status: ReturnStatus,
        target_status: ReturnStatus,
    ) -> bool:
        if not isinstance(current_status, ReturnStatus):
            raise ValueError(
                "Current status must be a ReturnStatus"
            )

        if not isinstance(target_status, ReturnStatus):
            raise ValueError(
                "Target status must be a ReturnStatus"
            )

        return target_status in self._TRANSITIONS[current_status]

    def transition(
        self,
        return_request: ReturnRequest,
        target_status: ReturnStatus,
        timestamp: datetime | None = None,
    ) -> None:
        if not isinstance(return_request, ReturnRequest):
            raise ValueError(
                "Return request must be a ReturnRequest"
            )

        if not isinstance(target_status, ReturnStatus):
            raise ValueError(
                "Target status must be a ReturnStatus"
            )

        if timestamp is not None and not isinstance(timestamp, datetime):
            raise ValueError(
                "Timestamp must be a datetime"
            )

        current_status = return_request.status

        if not self.can_transition(
            current_status,
            target_status,
        ):
            raise InvalidReturnStateError(
                return_request.return_id,
                current_status.value,
                target_status.value,
            )

        transition_timestamp = (
            timestamp
            if timestamp is not None
            else datetime.now()
        )

        return_request._set_status(
            target_status,
            transition_timestamp,
        )