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
