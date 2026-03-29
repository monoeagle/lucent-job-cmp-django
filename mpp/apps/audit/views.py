from django.views.generic import ListView

from core.mixins import AdminRequiredMixin

from .models import AuditLog


class AuditLogListView(AdminRequiredMixin, ListView):
    template_name = "audit/audit_list.html"
    context_object_name = "logs"
    paginate_by = 50

    def get_queryset(self):
        qs = AuditLog.objects.select_related("user").all()
        resource_type = self.request.GET.get("resource_type")
        if resource_type:
            qs = qs.filter(resource_type=resource_type)
        return qs
