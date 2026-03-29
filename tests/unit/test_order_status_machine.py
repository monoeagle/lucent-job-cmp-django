"""Test order status machine."""
import pytest
from core.domain.value_objects import OrderStatus, StatusMachine


class TestOrderStatus:
    def test_has_expected_statuses(self):
        expected = ["draft", "validated", "submitted", "pending_approval",
                    "approved", "rejected", "provisioning", "done", "failed"]
        assert len(OrderStatus.choices) == len(expected)
        for status in expected:
            assert hasattr(OrderStatus, status.upper())

    def test_draft_is_default(self):
        assert OrderStatus.DRAFT == "draft"


class TestStatusMachine:
    def test_draft_to_validated(self):
        assert StatusMachine.can_transition("draft", "validated") is True

    def test_validated_to_submitted(self):
        assert StatusMachine.can_transition("validated", "submitted") is True

    def test_submitted_to_pending_approval(self):
        assert StatusMachine.can_transition("submitted", "pending_approval") is True

    def test_submitted_to_approved(self):
        assert StatusMachine.can_transition("submitted", "approved") is True

    def test_pending_approval_to_approved(self):
        assert StatusMachine.can_transition("pending_approval", "approved") is True

    def test_pending_approval_to_rejected(self):
        assert StatusMachine.can_transition("pending_approval", "rejected") is True

    def test_approved_to_provisioning(self):
        assert StatusMachine.can_transition("approved", "provisioning") is True

    def test_provisioning_to_done(self):
        assert StatusMachine.can_transition("provisioning", "done") is True

    def test_provisioning_to_failed(self):
        assert StatusMachine.can_transition("provisioning", "failed") is True

    def test_done_is_terminal(self):
        assert StatusMachine.can_transition("done", "draft") is False
        assert StatusMachine.is_terminal("done") is True

    def test_failed_is_terminal(self):
        assert StatusMachine.is_terminal("failed") is True

    def test_rejected_is_terminal(self):
        assert StatusMachine.is_terminal("rejected") is True

    def test_draft_is_not_terminal(self):
        assert StatusMachine.is_terminal("draft") is False

    def test_invalid_transition_rejected(self):
        assert StatusMachine.can_transition("draft", "done") is False

    def test_get_allowed_transitions(self):
        allowed = StatusMachine.get_allowed_transitions("draft")
        assert "validated" in allowed
        assert "done" not in allowed

    def test_validate_transition_raises_on_invalid(self):
        with pytest.raises(ValueError):
            StatusMachine.validate_transition("draft", "done")
