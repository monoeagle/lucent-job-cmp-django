"""End-to-end test: full order lifecycle (service level)."""
import pytest
from apps.approvals.models import ApprovalRule
from apps.provisioning.models import DispatchLog
from apps.provisioning.services import ProvisioningService
from apps.approvals.services import ApprovalService
from apps.orders.services import OrderService
from apps.subscriptions.services import SubscriptionService
from core.domain.value_objects import OrderStatus
from tests.factories import UserFactory, ServiceTemplateFactory


@pytest.mark.django_db
class TestFullOrderWorkflow:
    def test_complete_lifecycle_without_approval(self):
        user = UserFactory()
        template = ServiceTemplateFactory(parameters=[
            {"key": "cpu", "type": "integer", "required": True},
        ])
        order = OrderService.create_order(user=user, notes="E2E test")
        OrderService.add_item(order.pk, template.pk, {"cpu": 4})
        order = OrderService.submit_order(order.pk, actor=user)
        # keine Regel -> auto-genehmigt
        assert order.status == OrderStatus.APPROVED

        ProvisioningService.dispatch_order(order.pk)
        order.refresh_from_db()
        assert order.status == OrderStatus.PROVISIONING

        log = DispatchLog.objects.get(order_item__order=order)
        ProvisioningService.complete_dispatch(log.pk, success=True)
        order.refresh_from_db()
        assert order.status == OrderStatus.DONE
        # Subscription automatisch angelegt
        assert SubscriptionService.list_user_subscriptions(user.pk)

    def test_complete_lifecycle_with_approval(self):
        user = UserFactory()
        approver = UserFactory(role="approver")
        template = ServiceTemplateFactory(parameters=[
            {"key": "cpu", "type": "integer", "required": True},
        ])
        ApprovalRule.objects.create(template=template, approver_role="approver")

        order = OrderService.create_order(user=user)
        OrderService.add_item(order.pk, template.pk, {"cpu": 8})
        order = OrderService.submit_order(order.pk, actor=user)
        order.refresh_from_db()
        assert order.status == OrderStatus.PENDING_APPROVAL

        from apps.approvals.models import ApprovalRequest
        req = ApprovalRequest.objects.get(order=order)
        ApprovalService.approve(req.pk, approver)
        order.refresh_from_db()
        assert order.status == OrderStatus.APPROVED

        ProvisioningService.dispatch_order(order.pk)
        log = DispatchLog.objects.get(order_item__order=order)
        ProvisioningService.complete_dispatch(log.pk, success=True)
        order.refresh_from_db()
        assert order.status == OrderStatus.DONE

    def test_rejected_order_workflow(self):
        user = UserFactory()
        approver = UserFactory(role="approver")
        template = ServiceTemplateFactory(parameters=[
            {"key": "cpu", "type": "integer", "required": True},
        ])
        ApprovalRule.objects.create(template=template, approver_role="approver")

        order = OrderService.create_order(user=user)
        OrderService.add_item(order.pk, template.pk, {"cpu": 2})
        OrderService.submit_order(order.pk, actor=user)
        from apps.approvals.models import ApprovalRequest
        req = ApprovalRequest.objects.get(order=order)
        ApprovalService.reject(req.pk, approver, comment="Budget exceeded")
        order.refresh_from_db()
        assert order.status == OrderStatus.REJECTED

    def test_failed_provisioning_workflow(self):
        user = UserFactory()
        template = ServiceTemplateFactory(parameters=[
            {"key": "cpu", "type": "integer", "required": True},
        ])
        order = OrderService.create_order(user=user)
        OrderService.add_item(order.pk, template.pk, {"cpu": 4})
        order = OrderService.submit_order(order.pk, actor=user)
        assert order.status == OrderStatus.APPROVED

        ProvisioningService.dispatch_order(order.pk)
        log = DispatchLog.objects.get(order_item__order=order)
        ProvisioningService.complete_dispatch(log.pk, success=False)
        order.refresh_from_db()
        assert order.status == OrderStatus.FAILED
