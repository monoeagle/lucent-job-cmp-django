"""End-to-end test: full order lifecycle."""
import pytest
from apps.approvals.models import ApprovalRule, ApprovalRequest
from apps.orders.models import Order
from apps.provisioning.models import DispatchLog
from apps.provisioning.services import ProvisioningService
from apps.approvals.services import ApprovalService
from apps.orders.services import OrderService
from apps.subscriptions.services import SubscriptionService
from core.domain.value_objects import OrderStatus
from tests.factories import UserFactory, ServiceTemplateFactory


@pytest.mark.django_db
class TestFullOrderWorkflow:
    """Test the complete order lifecycle: create -> submit -> approve -> provision -> subscribe."""

    def test_complete_lifecycle_without_approval(self):
        """Order without approval rules goes directly to approved."""
        user = UserFactory()
        template = ServiceTemplateFactory(parameters=[
            {"key": "cpu", "type": "integer", "required": True},
        ])
        # No approval rules -> order goes straight to approved

        # 1. Create order
        order = OrderService.create_order(user=user, notes="E2E test")
        assert order.status == OrderStatus.DRAFT

        # 2. Add item
        item = OrderService.add_item(order.pk, template.pk, {"cpu": 4})
        assert item.parameters == {"cpu": 4}

        # 3. Submit
        order = OrderService.submit_order(order.pk)
        assert order.status == OrderStatus.SUBMITTED

        # 4. No approval needed -> manually move to approved
        needs = ApprovalService.needs_approval(order.pk)
        assert needs is False
        order.status = OrderStatus.APPROVED
        order.save()

        # 5. Provision
        ProvisioningService.dispatch_order(order.pk)
        order.refresh_from_db()
        assert order.status == OrderStatus.PROVISIONING

        # 6. Complete provisioning
        log = DispatchLog.objects.get(order_item__order=order)
        ProvisioningService.complete_dispatch(log.pk, success=True)
        order.refresh_from_db()
        assert order.status == OrderStatus.DONE

        # 7. Create subscription
        subs = SubscriptionService.create_from_order(order.pk)
        assert len(subs) == 1
        assert subs[0].status == "active"

    def test_complete_lifecycle_with_approval(self):
        """Order with approval rules goes through pending_approval."""
        user = UserFactory()
        approver = UserFactory(role="approver")
        template = ServiceTemplateFactory(parameters=[
            {"key": "cpu", "type": "integer", "required": True},
        ])
        ApprovalRule.objects.create(template=template, approver_role="approver")

        # 1. Create + add item + submit
        order = OrderService.create_order(user=user)
        OrderService.add_item(order.pk, template.pk, {"cpu": 8})
        order = OrderService.submit_order(order.pk)

        # 2. Check needs approval
        assert ApprovalService.needs_approval(order.pk) is True

        # 3. Create approval requests
        requests = ApprovalService.create_approval_requests(order.pk)
        assert len(requests) == 1
        order.refresh_from_db()
        assert order.status == OrderStatus.PENDING_APPROVAL

        # 4. Approve
        ApprovalService.approve(requests[0].pk, approver)
        order.refresh_from_db()
        assert order.status == OrderStatus.APPROVED

        # 5. Provision
        ProvisioningService.dispatch_order(order.pk)
        order.refresh_from_db()
        assert order.status == OrderStatus.PROVISIONING

        log = DispatchLog.objects.get(order_item__order=order)
        ProvisioningService.complete_dispatch(log.pk, success=True)
        order.refresh_from_db()
        assert order.status == OrderStatus.DONE

    def test_rejected_order_workflow(self):
        """Order that gets rejected stays rejected."""
        user = UserFactory()
        approver = UserFactory(role="approver")
        template = ServiceTemplateFactory(parameters=[
            {"key": "cpu", "type": "integer", "required": True},
        ])
        ApprovalRule.objects.create(template=template, approver_role="approver")

        order = OrderService.create_order(user=user)
        OrderService.add_item(order.pk, template.pk, {"cpu": 2})
        OrderService.submit_order(order.pk)
        requests = ApprovalService.create_approval_requests(order.pk)
        ApprovalService.reject(requests[0].pk, approver, comment="Budget exceeded")

        order.refresh_from_db()
        assert order.status == OrderStatus.REJECTED

    def test_failed_provisioning_workflow(self):
        """Order where provisioning fails gets status failed."""
        user = UserFactory()
        template = ServiceTemplateFactory(parameters=[
            {"key": "cpu", "type": "integer", "required": True},
        ])

        order = OrderService.create_order(user=user)
        OrderService.add_item(order.pk, template.pk, {"cpu": 4})
        OrderService.submit_order(order.pk)
        order.status = OrderStatus.APPROVED
        order.save()

        ProvisioningService.dispatch_order(order.pk)
        log = DispatchLog.objects.get(order_item__order=order)
        ProvisioningService.complete_dispatch(log.pk, success=False)

        order.refresh_from_db()
        assert order.status == OrderStatus.FAILED
