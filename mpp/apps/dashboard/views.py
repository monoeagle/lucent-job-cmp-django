from django.views.generic import TemplateView

from apps.notifications.services import NotificationService
from apps.orders.models import Order
from core.mixins import RequesterRequiredMixin


class DashboardView(RequesterRequiredMixin, TemplateView):
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx["order_count"] = Order.objects.filter(user=user).count()
        ctx["unread_notifications"] = NotificationService.unread_count(user.pk)
        return ctx
