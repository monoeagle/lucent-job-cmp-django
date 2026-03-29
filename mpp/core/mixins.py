"""Shared model and view mixins."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base model with created_at and updated_at."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class RoleRequiredMixin(LoginRequiredMixin):
    """Mixin that restricts access to specific user roles."""
    required_roles: list[str] = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.required_roles and request.user.role not in self.required_roles:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
