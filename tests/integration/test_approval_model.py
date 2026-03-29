import pytest
from apps.approvals.models import ApprovalRule, ApprovalRequest
from tests.factories import UserFactory, ServiceTemplateFactory, OrderFactory

@pytest.mark.django_db
class TestApprovalRule:
    def test_create_rule(self):
        t = ServiceTemplateFactory()
        rule = ApprovalRule.objects.create(template=t, condition={"min_cpu": 8}, approver_role="approver")
        assert rule.pk is not None

    def test_str(self):
        t = ServiceTemplateFactory(name="Linux VM")
        rule = ApprovalRule.objects.create(template=t, approver_role="approver")
        assert "Linux VM" in str(rule)

    def test_default_condition_empty(self):
        t = ServiceTemplateFactory()
        rule = ApprovalRule.objects.create(template=t, approver_role="approver")
        assert rule.condition == {}

@pytest.mark.django_db
class TestApprovalRequest:
    def test_create_request(self):
        t = ServiceTemplateFactory()
        rule = ApprovalRule.objects.create(template=t, approver_role="approver")
        order = OrderFactory()
        req = ApprovalRequest.objects.create(order=order, rule=rule, status="pending")
        assert req.pk is not None

    def test_approve(self):
        t = ServiceTemplateFactory()
        rule = ApprovalRule.objects.create(template=t, approver_role="approver")
        order = OrderFactory()
        approver = UserFactory()
        req = ApprovalRequest.objects.create(order=order, rule=rule, status="pending")
        req.status = "approved"
        req.decided_by = approver
        req.save()
        assert req.status == "approved"

    def test_str(self):
        t = ServiceTemplateFactory()
        rule = ApprovalRule.objects.create(template=t, approver_role="approver")
        order = OrderFactory()
        req = ApprovalRequest.objects.create(order=order, rule=rule, status="pending")
        assert "pending" in str(req).lower()
