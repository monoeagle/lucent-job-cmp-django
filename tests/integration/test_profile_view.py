"""Test profile and dashboard views."""
import pytest
from django.urls import reverse
from core.domain.enums import UserRole
from tests.factories import UserFactory


@pytest.mark.django_db
class TestProfileView:
    def test_profile_requires_login(self, client):
        response = client.get(reverse("accounts:profile"))
        assert response.status_code == 302

    def test_profile_returns_200_for_authenticated_user(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("accounts:profile"))
        assert response.status_code == 200

    def test_profile_shows_username(self, client):
        user = UserFactory(username="test-requester")
        client.force_login(user)
        response = client.get(reverse("accounts:profile"))
        assert "test-requester" in response.content.decode()

    def test_profile_shows_role(self, client):
        user = UserFactory(username="testuser", role=UserRole.ADMIN)
        client.force_login(user)
        response = client.get(reverse("accounts:profile"))
        assert "admin" in response.content.decode().lower()


@pytest.mark.django_db
class TestDashboardView:
    def test_dashboard_requires_login(self, client):
        response = client.get(reverse("dashboard:home"))
        assert response.status_code == 302

    def test_dashboard_returns_200(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("dashboard:home"))
        assert response.status_code == 200

    def test_root_url_serves_dashboard(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get("/")
        assert response.status_code == 200
