import pytest
from django.urls import reverse

from apps.notifications.services import NotificationService
from tests.factories import UserFactory


@pytest.mark.django_db
class TestNotificationViews:
    def test_list_requires_login(self, client):
        assert client.get(reverse("notifications:list")).status_code == 302

    def test_list_returns_200(self, client):
        user = UserFactory()
        client.force_login(user)
        assert client.get(reverse("notifications:list")).status_code == 200

    def test_mark_read(self, client):
        user = UserFactory()
        n = NotificationService.create(user=user, title="T", message="m")
        client.force_login(user)
        response = client.post(reverse("notifications:mark_read", kwargs={"pk": n.pk}))
        assert response.status_code == 302
        n.refresh_from_db()
        assert n.is_read is True

    def test_mark_all_read(self, client):
        user = UserFactory()
        NotificationService.create(user=user, title="A", message="m")
        client.force_login(user)
        assert client.post(reverse("notifications:mark_all_read")).status_code == 302
