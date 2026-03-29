import pytest
from django.urls import reverse

from tests.factories import OrderFactory, UserFactory


@pytest.mark.django_db
class TestDashboardStats:
    def test_dashboard_shows_stats(self, client):
        user = UserFactory()
        OrderFactory(user=user)
        OrderFactory(user=user)
        client.force_login(user)
        response = client.get(reverse("dashboard:home"))
        assert response.status_code == 200
