"""Order domain models."""
from django.conf import settings
from django.db import models

from core.domain.value_objects import OrderStatus
from core.mixins import TimeStampedModel


class Order(TimeStampedModel):
    """A service order placed by a user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    status = models.CharField(
        max_length=30,
        choices=OrderStatus.choices,
        default=OrderStatus.DRAFT,
    )
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} ({self.status})"


class OrderItemGroup(TimeStampedModel):
    """A group of identical order items sharing parameters."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="groups"
    )
    template = models.ForeignKey(
        "catalog.ServiceTemplate", on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField(default=1)
    shared_parameters = models.JSONField(default=dict)

    class Meta:
        db_table = "order_item_groups"

    def __str__(self):
        return f"Group: {self.template.name} x{self.quantity}"


class OrderItem(TimeStampedModel):
    """A single item in an order, referencing a service template."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items"
    )
    template = models.ForeignKey(
        "catalog.ServiceTemplate", on_delete=models.PROTECT
    )
    parameters = models.JSONField(default=dict)
    group = models.ForeignKey(
        OrderItemGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
    )

    class Meta:
        db_table = "order_items"

    def __str__(self):
        return f"Item: {self.template.name}"
