"""Admin panel views (not Django admin — custom admin dashboard)."""
import json
from django.views.generic import TemplateView
from core.mixins import AdminRequiredMixin, SuperadminRequiredMixin
from apps.approvals.models import ApprovalRule
from apps.cmdb.models import AvailabilityRule, ContextRestriction, UserTenantAssignment
from .services import DashboardService


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = "admin_panel/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["stats"] = DashboardService.get_admin_stats()
        ctx["orders_by_status"] = json.dumps(
            DashboardService.get_orders_by_status()
        )
        ctx["orders_by_month"] = json.dumps(
            DashboardService.get_orders_by_month()
        )
        ctx["recent_orders"] = DashboardService.get_recent_orders(limit=10)
        return ctx


class AdminConfigView(AdminRequiredMixin, TemplateView):
    template_name = "admin_panel/config.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from django.conf import settings

        ctx["auth_mode"] = "allauth"
        ctx["cmdb_mode"] = "stub"
        ctx["db_host"] = settings.DATABASES["default"]["HOST"]
        ctx["db_name"] = settings.DATABASES["default"]["NAME"]
        ctx["celery_eager"] = getattr(
            settings, "CELERY_TASK_ALWAYS_EAGER", False
        )
        return ctx


class AdminRulesView(SuperadminRequiredMixin, TemplateView):
    template_name = "admin_panel/rules.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["approval_rules"] = ApprovalRule.objects.select_related(
            "template"
        ).all()
        ctx["availability_rules"] = AvailabilityRule.objects.select_related(
            "template"
        ).all()
        ctx["context_restrictions"] = ContextRestriction.objects.select_related(
            "template"
        ).all()
        ctx["tenant_assignments"] = UserTenantAssignment.objects.select_related(
            "user"
        ).all()
        return ctx
