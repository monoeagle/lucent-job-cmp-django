from django.conf import settings
from django.db import models

from core.mixins import TimeStampedModel


class AvailabilityRule(TimeStampedModel):
    template = models.ForeignKey(
        "catalog.ServiceTemplate",
        on_delete=models.CASCADE,
        related_name="availability_rules",
    )
    location = models.CharField(max_length=50, blank=True, default="")
    tenant = models.CharField(max_length=50, blank=True, default="")
    is_available = models.BooleanField(default=True)

    class Meta:
        db_table = "availability_rules"

    def __str__(self):
        return f"{self.template.name} @ {self.location or '*'}/{self.tenant or '*'}"


class ContextRestriction(TimeStampedModel):
    template = models.ForeignKey(
        "catalog.ServiceTemplate",
        on_delete=models.CASCADE,
        related_name="context_restrictions",
    )
    parameter_key = models.CharField(max_length=50)
    context_field = models.CharField(max_length=50)
    allowed_values = models.JSONField(default=list)

    class Meta:
        db_table = "context_restrictions"

    def __str__(self):
        return f"{self.template.name}: {self.parameter_key} restricted by {self.context_field}"


class UserTenantAssignment(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tenant_assignments",
    )
    tenant = models.CharField(max_length=50)

    class Meta:
        db_table = "user_tenant_assignments"
        unique_together = [("user", "tenant")]

    def __str__(self):
        return f"{self.user.username} → {self.tenant}"
