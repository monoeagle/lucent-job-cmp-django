"""Test OrderService."""
import pytest
from apps.orders.models import Order, OrderItem
from apps.orders.services import OrderService
from core.domain.value_objects import OrderStatus
from core.exceptions import ValidationError, NotFoundError, ConflictError
from tests.factories import UserFactory, ServiceTemplateFactory, OrderFactory, OrderItemFactory


@pytest.mark.django_db
class TestOrderServiceCreate:
    def test_create_order(self):
        user = UserFactory()
        order = OrderService.create_order(user=user, notes="Test")
        assert order.status == OrderStatus.DRAFT
        assert order.user == user

    def test_create_order_without_notes(self):
        user = UserFactory()
        order = OrderService.create_order(user=user)
        assert order.notes == ""


@pytest.mark.django_db
class TestOrderServiceAddItem:
    def test_add_item_to_draft_order(self):
        user = UserFactory()
        template = ServiceTemplateFactory(parameters=[{"key": "cpu", "type": "integer", "required": True}])
        order = OrderService.create_order(user=user)
        item = OrderService.add_item(order_id=order.pk, template_id=template.pk, parameters={"cpu": 4})
        assert item.order == order
        assert item.parameters == {"cpu": 4}

    def test_add_item_validates_parameters(self):
        user = UserFactory()
        template = ServiceTemplateFactory(parameters=[{"key": "cpu", "type": "integer", "required": True}])
        order = OrderService.create_order(user=user)
        with pytest.raises(ValidationError):
            OrderService.add_item(order_id=order.pk, template_id=template.pk, parameters={})

    def test_add_item_to_non_draft_raises(self):
        order = OrderFactory(status=OrderStatus.SUBMITTED)
        template = ServiceTemplateFactory()
        with pytest.raises(ConflictError):
            OrderService.add_item(order_id=order.pk, template_id=template.pk, parameters={"cpu": 2})

    def test_add_item_nonexistent_order_raises(self):
        template = ServiceTemplateFactory()
        with pytest.raises(NotFoundError):
            OrderService.add_item(order_id=99999, template_id=template.pk, parameters={})


@pytest.mark.django_db
class TestOrderServiceRemoveItem:
    def test_remove_item(self):
        item = OrderItemFactory()
        OrderService.remove_item(item_id=item.pk)
        assert OrderItem.objects.filter(pk=item.pk).count() == 0

    def test_remove_item_from_non_draft_raises(self):
        order = OrderFactory(status=OrderStatus.SUBMITTED)
        item = OrderItemFactory(order=order)
        with pytest.raises(ConflictError):
            OrderService.remove_item(item_id=item.pk)


@pytest.mark.django_db
class TestOrderServiceSubmit:
    def test_submit_order_with_items(self):
        order = OrderFactory()
        OrderItemFactory(order=order)
        result = OrderService.submit_order(order_id=order.pk, actor=order.user)
        assert result.status == OrderStatus.APPROVED

    def test_submit_empty_order_raises(self):
        order = OrderFactory()
        with pytest.raises(ValidationError):
            OrderService.submit_order(order_id=order.pk, actor=order.user)

    def test_submit_non_draft_raises(self):
        order = OrderFactory(status=OrderStatus.SUBMITTED)
        OrderItemFactory(order=order)
        with pytest.raises(ConflictError):
            OrderService.submit_order(order_id=order.pk, actor=order.user)


@pytest.mark.django_db
class TestOrderServiceSubmitWiring:
    def test_submit_without_rule_auto_approves(self):
        from apps.audit.models import AuditLog
        user = UserFactory(role="requester")
        template = ServiceTemplateFactory()
        order = OrderFactory(user=user)
        OrderItemFactory(order=order, template=template)
        result = OrderService.submit_order(order_id=order.pk, actor=user)
        assert result.status == OrderStatus.APPROVED
        assert AuditLog.objects.filter(
            resource_type="order", resource_id=order.pk, action="order.approved"
        ).exists()

    def test_submit_with_rule_goes_pending_and_notifies_approvers(self):
        from apps.approvals.models import ApprovalRule, ApprovalRequest
        from apps.notifications.models import Notification
        user = UserFactory(role="requester")
        approver = UserFactory(role="approver")
        template = ServiceTemplateFactory()
        ApprovalRule.objects.create(template=template, approver_role="approver")
        order = OrderFactory(user=user)
        OrderItemFactory(order=order, template=template)
        OrderService.submit_order(order_id=order.pk, actor=user)
        order.refresh_from_db()
        assert order.status == OrderStatus.PENDING_APPROVAL
        assert ApprovalRequest.objects.filter(order=order).count() == 1
        assert Notification.objects.filter(
            user=approver, title="Neue Genehmigung erforderlich"
        ).exists()


@pytest.mark.django_db
class TestOrderServiceGet:
    def test_get_order(self):
        order = OrderFactory()
        assert OrderService.get_order(order.pk).pk == order.pk

    def test_get_nonexistent_raises(self):
        with pytest.raises(NotFoundError):
            OrderService.get_order(99999)

    def test_list_user_orders(self):
        user = UserFactory()
        OrderFactory(user=user)
        OrderFactory(user=user)
        OrderFactory()
        assert len(OrderService.list_user_orders(user_id=user.pk)) == 2
