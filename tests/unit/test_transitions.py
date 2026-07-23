"""Test the central order transition helper."""
import pytest
from apps.audit.models import AuditLog
from apps.orders.transitions import transition
from core.domain.value_objects import OrderStatus
from tests.factories import UserFactory, OrderFactory


@pytest.mark.django_db
class TestTransition:
    def test_sets_status_and_saves(self):
        actor = UserFactory()
        order = OrderFactory(status=OrderStatus.DRAFT)
        transition(order, OrderStatus.VALIDATED, actor)
        order.refresh_from_db()
        assert order.status == OrderStatus.VALIDATED

    def test_writes_audit_log_with_from_and_action(self):
        actor = UserFactory()
        order = OrderFactory(status=OrderStatus.DRAFT)
        transition(order, OrderStatus.VALIDATED, actor)
        log = AuditLog.objects.get(resource_type="order", resource_id=order.pk)
        assert log.action == "order.validated"
        assert log.user == actor
        assert log.details["from"] == "draft"

    def test_merges_extra_details(self):
        actor = UserFactory()
        order = OrderFactory(status=OrderStatus.PENDING_APPROVAL)
        transition(order, OrderStatus.REJECTED, actor, comment="zu teuer")
        log = AuditLog.objects.get(resource_type="order", resource_id=order.pk)
        assert log.details["comment"] == "zu teuer"
        assert log.details["from"] == "pending_approval"

    def test_rejects_invalid_transition(self):
        actor = UserFactory()
        order = OrderFactory(status=OrderStatus.DRAFT)
        with pytest.raises(ValueError):
            transition(order, OrderStatus.DONE, actor)

    def test_actor_may_be_none(self):
        order = OrderFactory(status=OrderStatus.APPROVED)
        transition(order, OrderStatus.PROVISIONING, None)
        log = AuditLog.objects.get(resource_type="order", resource_id=order.pk)
        assert log.user is None
