from django.conf import settings
from django.db import models

from core.domain.enums import UserRole
from core.mixins import TimeStampedModel


class ApprovalRule(TimeStampedModel):
    """Rule that determines when an order requires approval."""

    template = models.ForeignKey(
        "catalog.ServiceTemplate",
        on_delete=models.CASCADE,
        related_name="approval_rules",
    )
    condition = models.JSONField(default=dict)
    # Freie Werte sind hier gefaehrlich: seit die Rolle bei der Entscheidung
    # geprueft wird, macht ein Wert ausserhalb der Rollenhierarchie die Anfrage
    # fuer niemanden entscheidbar.
    approver_role = models.CharField(
        max_length=20, choices=UserRole.choices, default=UserRole.APPROVER
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "approval_rules"

    def __str__(self):
        return f"Rule: {self.template.name} → {self.approver_role}"


class ApprovalRequest(TimeStampedModel):
    """Tracks an individual approval decision for an order."""

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="approval_requests",
    )
    rule = models.ForeignKey(ApprovalRule, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default="pending")
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    comment = models.TextField(blank=True, default="")

    class Meta:
        db_table = "approval_requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Approval #{self.pk} ({self.status}) for Order #{self.order_id}"
