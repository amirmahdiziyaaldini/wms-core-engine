from app.domain.exceptions.base import DomainError

class InvalidOrderStateError(DomainError):
    def __init__(self, order_id: str, current_state: str, attempted_action: str):
        self.order_id = order_id
        self.current_state = current_state
        self.attempted_action = attempted_action

        super().__init__(
            f"Invalid state for order {order_id}: "
            f"current state is {current_state}, "
            f"cannot perform action {attempted_action}"
        )