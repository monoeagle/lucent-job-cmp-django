from django.views.generic import TemplateView
from core.mixins import RequesterRequiredMixin


class DashboardView(RequesterRequiredMixin, TemplateView):
    template_name = "dashboard/dashboard.html"
