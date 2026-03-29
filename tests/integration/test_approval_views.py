import pytest
from django.urls import reverse
from apps.approvals.models import ApprovalRule, ApprovalRequest
from core.domain.enums import UserRole
from core.domain.value_objects import OrderStatus
from tests.factories import UserFactory, ServiceTemplateFactory, OrderFactory

@pytest.mark.django_db
class TestApprovalQueueView:
    def test_requires_login(self, client):
        response = client.get(reverse("approvals:queue"))
        assert response.status_code == 302

    def test_requester_forbidden(self, client):
        user = UserFactory(role=UserRole.REQUESTER)
        client.force_login(user)
        response = client.get(reverse("approvals:queue"))
        assert response.status_code == 403

    def test_approver_can_access(self, client):
        user = UserFactory(role=UserRole.APPROVER)
        client.force_login(user)
        response = client.get(reverse("approvals:queue"))
        assert response.status_code == 200

@pytest.mark.django_db
class TestApprovalActionViews:
    def test_approve(self, client):
        template = ServiceTemplateFactory()
        rule = ApprovalRule.objects.create(template=template, approver_role="approver")
        order = OrderFactory(status=OrderStatus.PENDING_APPROVAL)
        req = ApprovalRequest.objects.create(order=order, rule=rule, status="pending")
        user = UserFactory(role=UserRole.APPROVER)
        client.force_login(user)
        response = client.post(reverse("approvals:approve", kwargs={"pk": req.pk}))
        assert response.status_code == 302
        req.refresh_from_db()
        assert req.status == "approved"

    def test_reject(self, client):
        template = ServiceTemplateFactory()
        rule = ApprovalRule.objects.create(template=template, approver_role="approver")
        order = OrderFactory(status=OrderStatus.PENDING_APPROVAL)
        req = ApprovalRequest.objects.create(order=order, rule=rule, status="pending")
        user = UserFactory(role=UserRole.APPROVER)
        client.force_login(user)
        response = client.post(reverse("approvals:reject", kwargs={"pk": req.pk}), {"comment": "No"})
        assert response.status_code == 302
        req.refresh_from_db()
        assert req.status == "rejected"
