# tests/e2e/test_workflow_through_views.py
"""DoD-E2E: die komplette Bestellkette ausgeloest durch die Views."""
import pytest
from django.urls import reverse

from apps.approvals.models import ApprovalRule, ApprovalRequest
from apps.audit.models import AuditLog
from apps.notifications.models import Notification
from apps.subscriptions.models import Subscription
from core.domain.value_objects import OrderStatus
from tests.factories import (
    UserFactory, ServiceTemplateFactory, OrderFactory, OrderItemFactory,
)


@pytest.mark.django_db
class TestWorkflowThroughViews:
    def test_submit_approve_provision_done(self, client, django_capture_on_commit_callbacks):
        requester = UserFactory(role="requester")
        approver = UserFactory(role="approver")
        template = ServiceTemplateFactory(parameters=[
            {"key": "cpu", "type": "integer", "required": True},
        ])
        ApprovalRule.objects.create(template=template, approver_role="approver")
        order = OrderFactory(user=requester)
        OrderItemFactory(order=order, template=template, parameters={"cpu": 4})

        # --- einreichen durch den View ---
        client.force_login(requester)
        with django_capture_on_commit_callbacks(execute=True):
            r1 = client.post(reverse("orders:submit", kwargs={"pk": order.pk}))
        assert r1.status_code == 302
        order.refresh_from_db()
        assert order.status == OrderStatus.PENDING_APPROVAL
        req = ApprovalRequest.objects.get(order=order)
        assert req.status == "pending"
        assert Notification.objects.filter(
            user=approver, title="Neue Genehmigung erforderlich"
        ).exists()

        # --- genehmigen durch den View: on_commit feuert die ganze Kette ---
        client.force_login(approver)
        with django_capture_on_commit_callbacks(execute=True):
            r2 = client.post(reverse("approvals:approve", kwargs={"pk": req.pk}))
        assert r2.status_code == 302
        order.refresh_from_db()
        assert order.status == OrderStatus.DONE
        assert Subscription.objects.filter(user=requester).exists()
        assert AuditLog.objects.filter(
            resource_type="order", resource_id=order.pk, action="order.done"
        ).exists()
        assert Notification.objects.filter(
            user=requester, title="Bestellung abgeschlossen"
        ).exists()
