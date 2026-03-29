"""Test authentication views."""
import pytest
from django.urls import reverse
from tests.factories import UserFactory


@pytest.mark.django_db
class TestLoginView:
    def test_login_page_returns_200(self, client):
        response = client.get(reverse("account_login"))
        assert response.status_code == 200

    def test_login_page_uses_correct_template(self, client):
        response = client.get(reverse("account_login"))
        assert "account/login.html" in [t.name for t in response.templates]

    def test_login_with_valid_credentials_redirects(self, client):
        user = UserFactory(username="testuser")
        response = client.post(
            reverse("account_login"),
            {"login": "testuser", "password": "test123"},
        )
        assert response.status_code == 302

    def test_login_with_invalid_credentials_stays_on_page(self, client):
        response = client.post(
            reverse("account_login"),
            {"login": "nobody", "password": "wrong"},
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestLogoutView:
    def test_logout_redirects(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.post(reverse("account_logout"))
        assert response.status_code == 302
