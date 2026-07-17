"""Subscription domain models."""
from django.conf import settings
from django.db import models

from core.mixins import TimeStampedModel


class Subscription(TimeStampedModel):
    """A user's active subscription to a provisioned service."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    order_item = models.ForeignKey(
        "orders.OrderItem",
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    status = models.CharField(max_length=30, default="active")
    valid_from = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "subscriptions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Sub: {self.user.username} - {self.order_item.template.name} ({self.status})"


class GroupSubscription(TimeStampedModel):
    """A subscription tied to an order item group."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="group_subscriptions",
    )
    order_item_group = models.ForeignKey(
        "orders.OrderItemGroup",
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    status = models.CharField(max_length=30, default="active")

    class Meta:
        db_table = "group_subscriptions"

    def __str__(self):
        return f"GroupSub: {self.user.username} ({self.status})"
