"""Test domain enums."""
from core.domain.enums import UserRole


class TestUserRole:
    def test_has_four_roles(self):
        assert len(UserRole.choices) == 4

    def test_requester_value(self):
        assert UserRole.REQUESTER == "requester"
        assert UserRole.REQUESTER.label == "Requester"

    def test_approver_value(self):
        assert UserRole.APPROVER == "approver"
        assert UserRole.APPROVER.label == "Approver"

    def test_admin_value(self):
        assert UserRole.ADMIN == "admin"
        assert UserRole.ADMIN.label == "Admin"

    def test_superadmin_value(self):
        assert UserRole.SUPERADMIN == "superadmin"
        assert UserRole.SUPERADMIN.label == "Superadmin"
