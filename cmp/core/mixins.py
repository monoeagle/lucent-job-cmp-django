"""Shared model and view mixins."""
from django.core.exceptions import PermissionDenied
from django.db import models
from django.utils.module_loading import import_string


class TimeStampedModel(models.Model):
    """Abstract base model with created_at and updated_at."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


def _get_role_required_mixin_base():
    """Lazy-load LoginRequiredMixin to avoid circular imports at module level."""
    from django.contrib.auth.mixins import LoginRequiredMixin
    return LoginRequiredMixin


class RoleRequiredMixin:
    """Mixin that restricts access to specific user roles.

    Intended to be used alongside LoginRequiredMixin in views.
    The actual LoginRequiredMixin inheritance is deferred to avoid
    circular imports when models.py imports TimeStampedModel.
    """
    required_roles: list[str] = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.required_roles and request.user.role not in self.required_roles:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class _LazyLoginRequiredMixin:
    """Proxy that lazily inherits LoginRequiredMixin behavior at dispatch time.

    Direct inheritance from LoginRequiredMixin at module level causes circular
    imports (LoginRequiredMixin -> auth.views -> auth.forms -> get_user_model)
    when models.py imports TimeStampedModel from this module.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.conf import settings
            from django.shortcuts import redirect
            return redirect(settings.LOGIN_URL)
        return super().dispatch(request, *args, **kwargs)


def _lazy_roles():
    """Lazy-load UserRole to avoid importing during app loading."""
    from core.domain.enums import UserRole
    return UserRole


class RequesterRequiredMixin(_LazyLoginRequiredMixin, RoleRequiredMixin):
    """Any authenticated user (all roles can access)."""

    @property
    def required_roles(self):
        R = _lazy_roles()
        return [R.REQUESTER, R.APPROVER, R.ADMIN, R.SUPERADMIN]


class ApproverRequiredMixin(_LazyLoginRequiredMixin, RoleRequiredMixin):
    """Approver, Admin, or Superadmin."""

    @property
    def required_roles(self):
        R = _lazy_roles()
        return [R.APPROVER, R.ADMIN, R.SUPERADMIN]


class AdminRequiredMixin(_LazyLoginRequiredMixin, RoleRequiredMixin):
    """Admin or Superadmin."""

    @property
    def required_roles(self):
        R = _lazy_roles()
        return [R.ADMIN, R.SUPERADMIN]


class SuperadminRequiredMixin(_LazyLoginRequiredMixin, RoleRequiredMixin):
    """Superadmin only."""

    @property
    def required_roles(self):
        R = _lazy_roles()
        return [R.SUPERADMIN]
