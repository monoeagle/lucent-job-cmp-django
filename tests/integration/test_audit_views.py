import pytest
from django.urls import reverse

from core.domain.enums import UserRole
from tests.factories import UserFactory


@pytest.mark.django_db
class TestAuditViews:
    def test_requires_admin(self, client):
        user = UserFactory(role=UserRole.REQUESTER)
        client.force_login(user)
        assert client.get(reverse("audit:list")).status_code == 403

    def test_admin_can_access(self, client):
        user = UserFactory(role=UserRole.ADMIN)
        client.force_login(user)
        assert client.get(reverse("audit:list")).status_code == 200
