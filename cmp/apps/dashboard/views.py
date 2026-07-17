"""Dashboard views."""
from django.views.generic import TemplateView
from core.domain.enums import UserRole
from core.mixins import RequesterRequiredMixin
from apps.accounts.services import AccountService
from apps.notifications.services import NotificationService
from .services import DashboardService


class DashboardView(RequesterRequiredMixin, TemplateView):
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        # Admin/Superadmin see system-wide data, others see own data
        is_admin = AccountService.is_at_least_role(user.role, UserRole.ADMIN)
        scope_user = None if is_admin else user

        if is_admin:
            admin_stats = DashboardService.get_admin_stats()
            ctx["stats"] = {
                "open_orders": admin_stats.get("draft", 0) + admin_stats.get("submitted", 0) + admin_stats.get("pending_approval", 0),
                "pending_approvals": admin_stats.get("pending_approvals", 0),
                "active_subscriptions": admin_stats.get("total_subscriptions", 0),
                "total_templates": admin_stats.get("total_templates", 0),
                "unread_notifications": NotificationService.unread_count(user.pk),
            }
        else:
            ctx["stats"] = DashboardService.get_user_stats(user)
        ctx["orders_by_status"] = DashboardService.get_orders_by_status(user=scope_user)
        ctx["orders_by_month"] = DashboardService.get_orders_by_month(user=scope_user)
        ctx["recent_orders"] = DashboardService.get_recent_orders(user=scope_user)
        ctx["popular_templates"] = DashboardService.get_popular_templates()
        return ctx
