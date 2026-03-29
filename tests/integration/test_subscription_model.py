import pytest
from apps.subscriptions.models import Subscription, GroupSubscription
from apps.orders.models import OrderItemGroup, Order
from tests.factories import UserFactory, OrderItemFactory, ServiceTemplateFactory


@pytest.mark.django_db
class TestSubscriptionModel:
    def test_create(self):
        user = UserFactory()
        item = OrderItemFactory()
        s = Subscription.objects.create(user=user, order_item=item, status="active")
        assert s.pk is not None

    def test_str(self):
        user = UserFactory(username="testuser")
        item = OrderItemFactory()
        s = Subscription.objects.create(user=user, order_item=item, status="active")
        assert "testuser" in str(s)

    def test_valid_from_auto(self):
        user = UserFactory()
        item = OrderItemFactory()
        s = Subscription.objects.create(user=user, order_item=item, status="active")
        assert s.valid_from is not None

    def test_valid_until_nullable(self):
        user = UserFactory()
        item = OrderItemFactory()
        s = Subscription.objects.create(user=user, order_item=item, status="active")
        assert s.valid_until is None


@pytest.mark.django_db
class TestGroupSubscriptionModel:
    def test_create(self):
        user = UserFactory()
        template = ServiceTemplateFactory()
        order = Order.objects.create(user=user)
        group = OrderItemGroup.objects.create(order=order, template=template, quantity=3)
        gs = GroupSubscription.objects.create(user=user, order_item_group=group, status="active")
        assert gs.pk is not None
