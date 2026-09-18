from app.domain.exceptions.base import DomainError


class InvalidReturnStateError(DomainError):
    def __init__(
        self,
        return_id: str,
        current_state: str,
        attempted_action: str
    ):
        self.return_id = return_id
        self.current_state = current_state
        self.attempted_action = attempted_action

        super().__init__(
            f"Invalid state for return {return_id}: "
            f"current state is {current_state}, "
            f"cannot perform action {attempted_action}"
        )