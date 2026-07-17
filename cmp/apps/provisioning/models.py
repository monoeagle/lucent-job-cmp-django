"""Provisioning domain models."""
from django.db import models

from core.mixins import TimeStampedModel


class DispatchLog(TimeStampedModel):
    """Tracks a provisioning pipeline dispatch for an order item."""

    order_item = models.ForeignKey(
        "orders.OrderItem",
        on_delete=models.CASCADE,
        related_name="dispatch_logs",
    )
    pipeline_id = models.CharField(max_length=100)
    status = models.CharField(max_length=30, default="pending")
    payload = models.JSONField(default=dict)
    dispatched_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "dispatch_logs"
        ordering = ["-dispatched_at"]

    def __str__(self):
        return f"Dispatch {self.pipeline_id} ({self.status})"
