"""Audit views."""
import csv
from django.http import HttpResponse
from django.views import View
from django.views.generic import ListView
from core.mixins import AdminRequiredMixin
from .models import AuditLog


class AuditLogListView(AdminRequiredMixin, ListView):
    template_name = "audit/audit_list.html"
    context_object_name = "logs"
    paginate_by = 50

    def get_queryset(self):
        qs = AuditLog.objects.select_related("user").all()
        action = self.request.GET.get("action")
        resource_type = self.request.GET.get("resource_type")
        if action:
            qs = qs.filter(action__icontains=action)
        if resource_type:
            qs = qs.filter(resource_type__icontains=resource_type)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filter_action"] = self.request.GET.get("action", "")
        ctx["filter_resource_type"] = self.request.GET.get("resource_type", "")
        return ctx


class AuditLogExportView(AdminRequiredMixin, View):
    def get(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="audit-log.csv"'
        writer = csv.writer(response)
        writer.writerow([
            "Zeitpunkt", "Aktion", "Ressource",
            "Ressource-ID", "Benutzer", "Details",
        ])
        for log in AuditLog.objects.select_related("user").all():
            writer.writerow([
                log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                log.action,
                log.resource_type,
                log.resource_id,
                log.user.username if log.user else "\u2014",
                str(log.details),
            ])
        return response
