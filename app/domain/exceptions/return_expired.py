from app.domain.exceptions.base import DomainError

class ReturnExpiredError(DomainError):
    def __init__(self, return_id: str, deadline: str):
        self.return_id = return_id
        self.deadline = deadline

        super().__init__(
            f"Return request {return_id} has expired. "
            f"Deadline was {deadline}"
        )