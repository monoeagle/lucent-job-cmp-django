import pytest
from django.urls import reverse
from apps.subscriptions.models import Subscription
from core.domain.value_objects import OrderStatus
from tests.factories import UserFactory, OrderFactory, OrderItemFactory


@pytest.mark.django_db
class TestSubscriptionViews:
    def test_list_requires_login(self, client):
        assert client.get(reverse("subscriptions:list")).status_code == 302

    def test_list_returns_200(self, client):
        user = UserFactory()
        client.force_login(user)
        assert client.get(reverse("subscriptions:list")).status_code == 200

    def test_detail_returns_200(self, client):
        user = UserFactory()
        order = OrderFactory(user=user, status=OrderStatus.DONE)
        item = OrderItemFactory(order=order)
        sub = Subscription.objects.create(user=user, order_item=item, status="active")
        client.force_login(user)
        assert client.get(reverse("subscriptions:detail", kwargs={"pk": sub.pk})).status_code == 200

    def test_cancel(self, client):
        user = UserFactory()
        order = OrderFactory(user=user, status=OrderStatus.DONE)
        item = OrderItemFactory(order=order)
        sub = Subscription.objects.create(user=user, order_item=item, status="active")
        client.force_login(user)
        response = client.post(reverse("subscriptions:cancel", kwargs={"pk": sub.pk}))
        assert response.status_code == 302
        sub.refresh_from_db()
        assert sub.status == "cancelled"
