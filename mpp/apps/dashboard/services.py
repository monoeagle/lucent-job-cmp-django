"""Dashboard statistics service."""
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta

from apps.orders.models import Order
from apps.catalog.models import ServiceTemplate
from apps.subscriptions.models import Subscription
from apps.approvals.models import ApprovalRequest
from apps.notifications.services import NotificationService


class DashboardService:
    @staticmethod
    def get_user_stats(user):
        """Stats for the user dashboard."""
        orders = Order.objects.filter(user=user)
        return {
            "open_orders": orders.filter(
                status__in=["draft", "submitted", "pending_approval"]
            ).count(),
            "pending_approvals": ApprovalRequest.objects.filter(
                status="pending"
            ).count(),
            "active_subscriptions": Subscription.objects.filter(
                user=user, status="active"
            ).count(),
            "total_templates": ServiceTemplate.objects.filter(
                is_active=True
            ).count(),
            "unread_notifications": NotificationService.unread_count(user.pk),
        }

    @staticmethod
    def get_admin_stats():
        """Stats for the admin dashboard — system-wide."""
        status_counts = dict(
            Order.objects.values_list("status")
            .annotate(count=Count("id"))
            .values_list("status", "count")
        )
        return {
            "draft": status_counts.get("draft", 0),
            "submitted": status_counts.get("submitted", 0),
            "pending_approval": status_counts.get("pending_approval", 0),
            "approved": status_counts.get("approved", 0),
            "provisioning": status_counts.get("provisioning", 0),
            "done": status_counts.get("done", 0),
            "failed": status_counts.get("failed", 0),
            "rejected": status_counts.get("rejected", 0),
            "total_orders": Order.objects.count(),
            "total_templates": ServiceTemplate.objects.filter(
                is_active=True
            ).count(),
            "total_subscriptions": Subscription.objects.filter(
                status="active"
            ).count(),
            "pending_approvals": ApprovalRequest.objects.filter(
                status="pending"
            ).count(),
        }

    @staticmethod
    def get_orders_by_status(user=None):
        """For donut chart — list of {status, count}."""
        qs = Order.objects.all()
        if user:
            qs = qs.filter(user=user)
        counts = qs.values("status").annotate(count=Count("id")).order_by("status")
        return list(counts)

    @staticmethod
    def get_orders_by_month(user=None, months=6):
        """For line chart — list of {month, count}."""
        since = timezone.now() - timedelta(days=months * 30)
        qs = Order.objects.filter(created_at__gte=since)
        if user:
            qs = qs.filter(user=user)
        monthly = (
            qs.annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )
        return [
            {"month": m["month"].strftime("%Y-%m"), "count": m["count"]}
            for m in monthly
        ]

    @staticmethod
    def get_recent_orders(user=None, limit=5):
        """Return most recent orders, optionally filtered by user."""
        qs = Order.objects.select_related("user").all()
        if user:
            qs = qs.filter(user=user)
        return list(qs[:limit])

    @staticmethod
    def get_popular_templates(limit=5):
        """Return templates ordered by number of order items."""
        from apps.orders.models import OrderItem

        popular = (
            OrderItem.objects.values(
                "template_id", "template__name", "template__category"
            )
            .annotate(order_count=Count("id"))
            .order_by("-order_count")[:limit]
        )
        return list(popular)
