"""Domain value objects — OrderStatus enum and StatusMachine."""
from django.db import models


class OrderStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    VALIDATED = "validated", "Validated"
    SUBMITTED = "submitted", "Submitted"
    PENDING_APPROVAL = "pending_approval", "Pending Approval"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    PROVISIONING = "provisioning", "Provisioning"
    DONE = "done", "Done"
    FAILED = "failed", "Failed"


TRANSITIONS = {
    OrderStatus.DRAFT: [OrderStatus.VALIDATED],
    OrderStatus.VALIDATED: [OrderStatus.SUBMITTED],
    OrderStatus.SUBMITTED: [OrderStatus.PENDING_APPROVAL, OrderStatus.APPROVED],
    OrderStatus.PENDING_APPROVAL: [OrderStatus.APPROVED, OrderStatus.REJECTED],
    OrderStatus.APPROVED: [OrderStatus.PROVISIONING],
    OrderStatus.PROVISIONING: [OrderStatus.DONE, OrderStatus.FAILED],
    OrderStatus.REJECTED: [],
    OrderStatus.DONE: [],
    OrderStatus.FAILED: [],
}

TERMINAL_STATES = {OrderStatus.DONE, OrderStatus.FAILED, OrderStatus.REJECTED}


class StatusMachine:
    """Validates order status transitions."""

    @staticmethod
    def can_transition(from_status, to_status):
        """Check if a transition is allowed."""
        return to_status in TRANSITIONS.get(from_status, [])

    @staticmethod
    def is_terminal(status):
        """Check if a status is terminal (no further transitions)."""
        return status in TERMINAL_STATES

    @staticmethod
    def get_allowed_transitions(status):
        """Return list of statuses reachable from the given status."""
        return list(TRANSITIONS.get(status, []))

    @staticmethod
    def validate_transition(from_status, to_status):
        """Raise ValueError if transition is not allowed."""
        if not StatusMachine.can_transition(from_status, to_status):
            raise ValueError(
                f"Invalid transition: {from_status} \u2192 {to_status}"
            )
