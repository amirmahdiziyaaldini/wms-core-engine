from datetime import datetime

from app.domain.enums.qc_result import QCResult
from app.domain.enums.return_status import ReturnStatus
from app.domain.models.return_request import ReturnRequest


class QCService:

    def record_result(
        self,
        return_request: ReturnRequest,
        result: QCResult,
        note: str | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        if not isinstance(return_request, ReturnRequest):
            raise ValueError(
                "Return request must be a ReturnRequest"
            )

        if not isinstance(result, QCResult):
            raise ValueError(
                "QC result must be a QCResult"
            )

        if return_request.status != ReturnStatus.QC_INSPECTION:
            raise ValueError(
                "QC result can only be recorded during QC inspection"
            )

        qc_timestamp = (
            timestamp
            if timestamp is not None
            else datetime.now()
        )

        return_request.set_qc_result(
            result=result,
            note=note,
            timestamp=qc_timestamp,
        )