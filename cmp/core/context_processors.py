"""Context processors for template rendering."""
from apps.notifications.services import NotificationService
from apps.approvals.models import ApprovalRequest


def badge_counts(request):
    """Add notification and approval badge counts to every template."""
    if not request.user.is_authenticated:
        return {}

    # Import here to avoid circular imports
    from apps.orders.models import Order

    return {
        "unread_notification_count": NotificationService.unread_count(
            request.user.pk
        ),
        "pending_approval_count": ApprovalRequest.objects.filter(
            status="pending"
        ).count(),
        "open_order_count": Order.objects.filter(
            user=request.user, status__in=["draft", "submitted"]
        ).count(),
    }
