import pytest
from apps.approvals.models import ApprovalRule, ApprovalRequest
from apps.approvals.services import ApprovalService
from core.domain.value_objects import OrderStatus
from core.exceptions import ConflictError, NotFoundError
from tests.factories import UserFactory, ServiceTemplateFactory, OrderFactory, OrderItemFactory

@pytest.mark.django_db
class TestApprovalServiceCheckRules:
    def test_no_rules_returns_false(self):
        order = OrderFactory(status=OrderStatus.SUBMITTED)
        OrderItemFactory(order=order)
        assert ApprovalService.needs_approval(order.pk) is False

    def test_matching_rule_returns_true(self):
        template = ServiceTemplateFactory()
        ApprovalRule.objects.create(template=template, approver_role="approver")
        order = OrderFactory(status=OrderStatus.SUBMITTED)
        OrderItemFactory(order=order, template=template)
        assert ApprovalService.needs_approval(order.pk) is True

    def test_inactive_rule_ignored(self):
        template = ServiceTemplateFactory()
        ApprovalRule.objects.create(template=template, approver_role="approver", is_active=False)
        order = OrderFactory(status=OrderStatus.SUBMITTED)
        OrderItemFactory(order=order, template=template)
        assert ApprovalService.needs_approval(order.pk) is False

@pytest.mark.django_db
class TestApprovalServiceCreate:
    def test_create_approval_request(self):
        template = ServiceTemplateFactory()
        ApprovalRule.objects.create(template=template, approver_role="approver")
        order = OrderFactory(status=OrderStatus.SUBMITTED)
        OrderItemFactory(order=order, template=template)
        requests = ApprovalService.create_approval_requests(order.pk)
        assert len(requests) == 1
        assert requests[0].status == "pending"
        order.refresh_from_db()
        assert order.status == OrderStatus.PENDING_APPROVAL

@pytest.mark.django_db
class TestApprovalServiceDecide:
    def test_approve_order(self):
        template = ServiceTemplateFactory()
        rule = ApprovalRule.objects.create(template=template, approver_role="approver")
        order = OrderFactory(status=OrderStatus.PENDING_APPROVAL)
        req = ApprovalRequest.objects.create(order=order, rule=rule, status="pending")
        approver = UserFactory(role="approver")
        ApprovalService.approve(req.pk, approver)
        req.refresh_from_db()
        assert req.status == "approved"
        order.refresh_from_db()
        assert order.status == OrderStatus.APPROVED

    def test_reject_order(self):
        template = ServiceTemplateFactory()
        rule = ApprovalRule.objects.create(template=template, approver_role="approver")
        order = OrderFactory(status=OrderStatus.PENDING_APPROVAL)
        req = ApprovalRequest.objects.create(order=order, rule=rule, status="pending")
        approver = UserFactory(role="approver")
        ApprovalService.reject(req.pk, approver, comment="Not needed")
        req.refresh_from_db()
        assert req.status == "rejected"
        order.refresh_from_db()
        assert order.status == OrderStatus.REJECTED

    def test_approve_already_decided_raises(self):
        template = ServiceTemplateFactory()
        rule = ApprovalRule.objects.create(template=template, approver_role="approver")
        order = OrderFactory(status=OrderStatus.PENDING_APPROVAL)
        req = ApprovalRequest.objects.create(order=order, rule=rule, status="approved")
        approver = UserFactory(role="approver")
        with pytest.raises(ConflictError):
            ApprovalService.approve(req.pk, approver)

    def test_list_pending_requests(self):
        template = ServiceTemplateFactory()
        rule = ApprovalRule.objects.create(template=template, approver_role="approver")
        order = OrderFactory(status=OrderStatus.PENDING_APPROVAL)
        ApprovalRequest.objects.create(order=order, rule=rule, status="pending")
        ApprovalRequest.objects.create(order=order, rule=rule, status="approved")
        pending = ApprovalService.list_pending_requests()
        assert len(pending) == 1
