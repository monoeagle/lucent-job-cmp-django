"""Dashboard views."""
from django.views.generic import TemplateView
from core.mixins import RequesterRequiredMixin
from .services import DashboardService


class DashboardView(RequesterRequiredMixin, TemplateView):
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx["stats"] = DashboardService.get_user_stats(user)
        ctx["orders_by_status"] = DashboardService.get_orders_by_status(user=user)
        ctx["orders_by_month"] = DashboardService.get_orders_by_month(user=user)
        ctx["recent_orders"] = DashboardService.get_recent_orders(user=user)
        ctx["popular_templates"] = DashboardService.get_popular_templates()
        return ctx
