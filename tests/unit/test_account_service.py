"""Test AccountService."""
import pytest
from apps.accounts.models import User
from apps.accounts.services import AccountService
from core.domain.enums import UserRole


@pytest.mark.django_db
class TestAccountService:
    def test_seed_creates_five_stub_users(self):
        created = AccountService.seed_stub_users()
        assert created == 5
        assert User.objects.count() == 5

    def test_seed_is_idempotent(self):
        AccountService.seed_stub_users()
        created = AccountService.seed_stub_users()
        assert created == 0
        assert User.objects.count() == 5

    def test_seed_creates_correct_roles(self):
        AccountService.seed_stub_users()
        assert User.objects.get(username="test-requester").role == UserRole.REQUESTER
        assert User.objects.get(username="test-approver").role == UserRole.APPROVER
        assert User.objects.get(username="test-admin").role == UserRole.ADMIN
        assert User.objects.get(username="test-multi").role == UserRole.APPROVER
        assert User.objects.get(username="test-superadmin").role == UserRole.SUPERADMIN

    def test_seed_users_can_authenticate(self):
        AccountService.seed_stub_users()
        user = User.objects.get(username="test-requester")
        assert user.check_password("test123")

    def test_is_at_least_role_requester(self):
        assert AccountService.is_at_least_role(UserRole.REQUESTER, UserRole.REQUESTER) is True
        assert AccountService.is_at_least_role(UserRole.APPROVER, UserRole.REQUESTER) is True
        assert AccountService.is_at_least_role(UserRole.ADMIN, UserRole.REQUESTER) is True

    def test_is_at_least_role_admin(self):
        assert AccountService.is_at_least_role(UserRole.REQUESTER, UserRole.ADMIN) is False
        assert AccountService.is_at_least_role(UserRole.APPROVER, UserRole.ADMIN) is False
        assert AccountService.is_at_least_role(UserRole.ADMIN, UserRole.ADMIN) is True
        assert AccountService.is_at_least_role(UserRole.SUPERADMIN, UserRole.ADMIN) is True
