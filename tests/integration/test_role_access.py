"""Test role-based access control."""
import pytest
from django.http import HttpResponse
from django.views import View

from core.domain.enums import UserRole
from core.mixins import (
    RoleRequiredMixin,
    RequesterRequiredMixin,
    ApproverRequiredMixin,
    AdminRequiredMixin,
    SuperadminRequiredMixin,
)
from tests.factories import UserFactory


class RequesterView(RequesterRequiredMixin, View):
    def get(self, request):
        return HttpResponse("ok")


class ApproverView(ApproverRequiredMixin, View):
    def get(self, request):
        return HttpResponse("ok")


class AdminView(AdminRequiredMixin, View):
    def get(self, request):
        return HttpResponse("ok")


class SuperadminView(SuperadminRequiredMixin, View):
    def get(self, request):
        return HttpResponse("ok")


@pytest.mark.django_db
class TestRequesterAccess:
    def test_requester_can_access(self, rf):
        user = UserFactory(role=UserRole.REQUESTER)
        request = rf.get("/")
        request.user = user
        response = RequesterView.as_view()(request)
        assert response.status_code == 200

    def test_approver_can_access_requester_views(self, rf):
        user = UserFactory(role=UserRole.APPROVER)
        request = rf.get("/")
        request.user = user
        response = RequesterView.as_view()(request)
        assert response.status_code == 200

    def test_admin_can_access_requester_views(self, rf):
        user = UserFactory(role=UserRole.ADMIN)
        request = rf.get("/")
        request.user = user
        response = RequesterView.as_view()(request)
        assert response.status_code == 200


@pytest.mark.django_db
class TestApproverAccess:
    def test_requester_cannot_access_approver_views(self, rf):
        user = UserFactory(role=UserRole.REQUESTER)
        request = rf.get("/")
        request.user = user
        with pytest.raises(Exception):
            ApproverView.as_view()(request)

    def test_approver_can_access(self, rf):
        user = UserFactory(role=UserRole.APPROVER)
        request = rf.get("/")
        request.user = user
        response = ApproverView.as_view()(request)
        assert response.status_code == 200


@pytest.mark.django_db
class TestAdminAccess:
    def test_requester_cannot_access_admin_views(self, rf):
        user = UserFactory(role=UserRole.REQUESTER)
        request = rf.get("/")
        request.user = user
        with pytest.raises(Exception):
            AdminView.as_view()(request)

    def test_approver_cannot_access_admin_views(self, rf):
        user = UserFactory(role=UserRole.APPROVER)
        request = rf.get("/")
        request.user = user
        with pytest.raises(Exception):
            AdminView.as_view()(request)

    def test_admin_can_access(self, rf):
        user = UserFactory(role=UserRole.ADMIN)
        request = rf.get("/")
        request.user = user
        response = AdminView.as_view()(request)
        assert response.status_code == 200

    def test_superadmin_can_access_admin_views(self, rf):
        user = UserFactory(role=UserRole.SUPERADMIN)
        request = rf.get("/")
        request.user = user
        response = AdminView.as_view()(request)
        assert response.status_code == 200


@pytest.mark.django_db
class TestSuperadminAccess:
    def test_admin_cannot_access_superadmin_views(self, rf):
        user = UserFactory(role=UserRole.ADMIN)
        request = rf.get("/")
        request.user = user
        with pytest.raises(Exception):
            SuperadminView.as_view()(request)

    def test_superadmin_can_access(self, rf):
        user = UserFactory(role=UserRole.SUPERADMIN)
        request = rf.get("/")
        request.user = user
        response = SuperadminView.as_view()(request)
        assert response.status_code == 200
