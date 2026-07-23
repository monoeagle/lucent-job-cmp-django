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
        assert response.status_code == 200
        sichtbar = list(response.context["orders"])
        assert len(sichtbar) == 1
        assert sichtbar[0].user_id == user.pk


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

    def test_wizard_get_returns_200(self, client):
        """Wizard GET renders the first step (context)."""
        user = UserFactory()
        template = ServiceTemplateFactory()
        client.force_login(user)
        response = client.get(
            reverse("orders:create", kwargs={"template_pk": template.pk}),
        )
        assert response.status_code == 200
        assert "Kontext" in response.content.decode()

    def test_wizard_step_navigation(self, client):
        """Wizard POST with action=next advances to next step."""
        user = UserFactory()
        template = ServiceTemplateFactory()
        client.force_login(user)
        url = reverse("orders:create", kwargs={"template_pk": template.pk})
        # GET first step to init session
        client.get(url)
        # POST context step with valid data
        response = client.post(url, {
            "action": "next",
            "location": "loc-fra",
            "tenant": "tenant-alpha",
            "security_zone": "production",
        })
        assert response.status_code == 302

    def test_wizard_submit_creates_order(self, client):
        """Full wizard submit creates an order with item."""
        user = UserFactory()
        template = ServiceTemplateFactory(parameters=[
            {"key": "cpu", "type": "integer", "required": True, "group": "Compute"},
        ])
        client.force_login(user)
        url = reverse("orders:create", kwargs={"template_pk": template.pk})

        # Step 0: GET to init session
        client.get(url)

        # Step 0: POST context
        client.post(url, {
            "action": "next",
            "location": "loc-fra",
            "tenant": "tenant-alpha",
            "security_zone": "production",
        })

        # Step 1: POST parameters (navigate to step 1 first)
        client.get(url + "?step=1")
        client.post(url, {
            "action": "next",
            "cpu": "4",
        })

        # Step 2 (summary): POST submit
        client.get(url + "?step=2")
        response = client.post(url, {
            "action": "submit",
            "quantity": "1",
        })
        assert response.status_code == 302

        from apps.orders.models import Order
        order = Order.objects.filter(user=user).first()
        assert order is not None
        assert order.items.count() == 1


@pytest.mark.django_db
class TestOrderFormView:
    def test_submit_with_location_param_creates_order(self, client):
        """A template whose own required param is keyed 'location' must still
        validate: the context-stripping must not drop a real template parameter.

        Regression: 'location' collides with a context field key, so the view
        stripped it before validation -> 'Parameter validation failed'.
        """
        user = UserFactory()
        template = ServiceTemplateFactory(parameters=[
            {
                "key": "location",
                "type": "enum",
                "label": "Standort",
                "required": True,
                "constraints": {"options": [
                    {"value": "standort2", "label": "Standort2", "enabled": True},
                ]},
            },
        ])
        client.force_login(user)
        url = reverse("orders:create_form", kwargs={"template_pk": template.pk})
        response = client.post(url, {
            "tenant": "tenant-alpha",
            "security_zone": "development",
            "location": "standort2",
            "quantity": "1",
        })

        assert response.status_code == 302
        from apps.orders.models import Order
        order = Order.objects.filter(user=user).first()
        assert order is not None
        assert order.items.count() == 1
        assert order.items.first().parameters["location"] == "standort2"


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
        assert order.status == OrderStatus.APPROVED

    def test_submit_empty_order_stays_draft(self, client):
        user = UserFactory()
        order = OrderFactory(user=user)
        client.force_login(user)
        response = client.post(reverse("orders:submit", kwargs={"pk": order.pk}))
        order.refresh_from_db()
        assert order.status == OrderStatus.DRAFT
