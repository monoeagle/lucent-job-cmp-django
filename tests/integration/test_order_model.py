"""Test Order models."""
import pytest
from apps.orders.models import Order, OrderItem, OrderItemGroup
from core.domain.value_objects import OrderStatus
from tests.factories import UserFactory, ServiceTemplateFactory


@pytest.mark.django_db
class TestOrderModel:
    def test_create_order(self):
        user = UserFactory()
        order = Order.objects.create(user=user, notes="Test order")
        assert order.pk is not None
        assert order.status == OrderStatus.DRAFT

    def test_str_returns_id_and_status(self):
        user = UserFactory()
        order = Order.objects.create(user=user)
        assert f"Order #{order.pk}" in str(order)

    def test_has_timestamps(self):
        user = UserFactory()
        order = Order.objects.create(user=user)
        assert order.created_at is not None

    def test_ordering_by_created_at_desc(self):
        user = UserFactory()
        o1 = Order.objects.create(user=user, notes="first")
        o2 = Order.objects.create(user=user, notes="second")
        orders = list(Order.objects.all())
        assert orders[0].pk == o2.pk


@pytest.mark.django_db
class TestOrderItemModel:
    def test_create_order_item(self):
        user = UserFactory()
        template = ServiceTemplateFactory()
        order = Order.objects.create(user=user)
        item = OrderItem.objects.create(order=order, template=template, parameters={"cpu": 4})
        assert item.pk is not None

    def test_item_belongs_to_order(self):
        user = UserFactory()
        template = ServiceTemplateFactory()
        order = Order.objects.create(user=user)
        OrderItem.objects.create(order=order, template=template)
        assert order.items.count() == 1

    def test_str_returns_template_name(self):
        user = UserFactory()
        template = ServiceTemplateFactory(name="Linux VM")
        order = Order.objects.create(user=user)
        item = OrderItem.objects.create(order=order, template=template)
        assert "Linux VM" in str(item)


@pytest.mark.django_db
class TestOrderItemGroupModel:
    def test_create_group(self):
        user = UserFactory()
        template = ServiceTemplateFactory()
        order = Order.objects.create(user=user)
        group = OrderItemGroup.objects.create(order=order, template=template, quantity=3, shared_parameters={"cpu": 2})
        assert group.pk is not None
        assert group.quantity == 3

    def test_item_can_belong_to_group(self):
        user = UserFactory()
        template = ServiceTemplateFactory()
        order = Order.objects.create(user=user)
        group = OrderItemGroup.objects.create(order=order, template=template, quantity=2)
        item = OrderItem.objects.create(order=order, template=template, group=group)
        assert item.group == group
        assert group.items.count() == 1
