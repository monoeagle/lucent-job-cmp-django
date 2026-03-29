"""Test User model."""
import pytest
from apps.accounts.models import User
from core.domain.enums import UserRole
from tests.factories import UserFactory


@pytest.mark.django_db
class TestUserModel:
    def test_create_user_with_default_role(self):
        user = UserFactory()
        assert user.role == UserRole.REQUESTER
        assert user.pk is not None

    def test_create_user_with_approver_role(self):
        user = UserFactory(role=UserRole.APPROVER)
        assert user.role == UserRole.APPROVER

    def test_create_user_with_admin_role(self):
        user = UserFactory(role=UserRole.ADMIN)
        assert user.role == UserRole.ADMIN

    def test_create_user_with_superadmin_role(self):
        user = UserFactory(role=UserRole.SUPERADMIN)
        assert user.role == UserRole.SUPERADMIN

    def test_user_str_returns_username(self):
        user = UserFactory(username="test-requester")
        assert str(user) == "test-requester"

    def test_user_has_timestamps(self):
        user = UserFactory()
        assert user.created_at is not None
        assert user.updated_at is not None
