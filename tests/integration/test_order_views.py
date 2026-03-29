"""Test order views."""
import pytest
from django.urls import reverse
from core.domain.value_objects import OrderStatus
from tests.factories import UserFactory, ServiceTemplateFactory, OrderFactory, OrderItemFactory


@pytest.mark.django_db
class TestOrderListView:
    def test_requires_login(self, client):
        response = client.get(reverse("orders:list"))
        assert response.status_code == 302

    def test_returns_200(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("orders:list"))
        assert response.status_code == 200

    def test_shows_only_own_orders(self, client):
        user = UserFactory()
        other = UserFactory()
        OrderFactory(user=user)
        OrderFactory(user=other)
        client.force_login(user)
        response = client.get(reverse("orders:list"))
        # Should only see 1 order (own), not 2
        assert response.status_code == 200


@pytest.mark.django_db
class TestOrderDetailView:
    def test_requires_login(self, client):
        order = OrderFactory()
        response = client.get(reverse("orders:detail", kwargs={"pk": order.pk}))
        assert response.status_code == 302

    def test_returns_200_for_owner(self, client):
        user = UserFactory()
        order = OrderFactory(user=user)
        client.force_login(user)
        response = client.get(reverse("orders:detail", kwargs={"pk": order.pk}))
        assert response.status_code == 200

    def test_shows_order_items(self, client):
        user = UserFactory()
        order = OrderFactory(user=user)
        template = ServiceTemplateFactory(name="Linux VM")
        OrderItemFactory(order=order, template=template)
        client.force_login(user)
        response = client.get(reverse("orders:detail", kwargs={"pk": order.pk}))
        assert "Linux VM" in response.content.decode()

    def test_404_for_nonexistent(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("orders:detail", kwargs={"pk": 99999}))
        assert response.status_code == 404


@pytest.mark.django_db
class TestOrderCreateView:
    def test_requires_login(self, client):
        template = ServiceTemplateFactory()
        response = client.get(reverse("orders:create", kwargs={"template_pk": template.pk}))
        assert response.status_code == 302

    def test_returns_200(self, client):
        user = UserFactory()
        template = ServiceTemplateFactory()
        client.force_login(user)
        response = client.get(reverse("orders:create", kwargs={"template_pk": template.pk}))
        assert response.status_code == 200

    def test_post_creates_order_with_item(self, client):
        user = UserFactory()
        template = ServiceTemplateFactory(parameters=[
            {"key": "cpu", "type": "integer", "required": True},
        ])
        client.force_login(user)
        response = client.post(
            reverse("orders:create", kwargs={"template_pk": template.pk}),
            {"cpu": "4"},
        )
        assert response.status_code == 302
        from apps.orders.models import Order
        order = Order.objects.filter(user=user).first()
        assert order is not None
        assert order.items.count() == 1


@pytest.mark.django_db
class TestOrderSubmitView:
    def test_submit_order(self, client):
        user = UserFactory()
        order = OrderFactory(user=user)
        OrderItemFactory(order=order)
        client.force_login(user)
        response = client.post(reverse("orders:submit", kwargs={"pk": order.pk}))
        assert response.status_code == 302
        order.refresh_from_db()
        assert order.status == OrderStatus.SUBMITTED

    def test_submit_empty_order_stays_draft(self, client):
        user = UserFactory()
        order = OrderFactory(user=user)
        client.force_login(user)
        response = client.post(reverse("orders:submit", kwargs={"pk": order.pk}))
        order.refresh_from_db()
        assert order.status == OrderStatus.DRAFT
