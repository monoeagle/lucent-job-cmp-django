"""Service layer for the subscriptions app."""
from django.utils import timezone

from apps.orders.services import OrderService
from apps.subscriptions.models import Subscription
from core.domain.value_objects import OrderStatus
from core.exceptions import ConflictError, NotFoundError


class SubscriptionService:
    """Application service for subscription operations."""

    @staticmethod
    def create_from_order(order_id):
        """Create subscriptions for all items of a completed order."""
        order = OrderService.get_order(order_id)
        if order.status != OrderStatus.DONE:
            raise ConflictError(
                "Subscriptions can only be created from completed orders."
            )
        subs = []
        for item in order.items.all():
            sub = Subscription.objects.create(
                user=order.user, order_item=item, status="active"
            )
            subs.append(sub)
        return subs

    @staticmethod
    def list_user_subscriptions(user_id):
        """Return all subscriptions for a given user."""
        return list(
            Subscription.objects.filter(user_id=user_id)
            .select_related("order_item__template")
        )

    @staticmethod
    def get_subscription(sub_id):
        """Get a subscription by ID or raise NotFoundError."""
        try:
            return Subscription.objects.get(pk=sub_id)
        except Subscription.DoesNotExist:
            raise NotFoundError(f"Subscription {sub_id} not found.")

    @staticmethod
    def cancel(sub_id):
        """Cancel an active subscription."""
        sub = SubscriptionService.get_subscription(sub_id)
        if sub.status != "active":
            raise ConflictError(
                f"Cannot cancel subscription in status '{sub.status}'."
            )
        sub.status = "cancelled"
        sub.valid_until = timezone.now()
        sub.save()
