"""Approval views."""
from django.contrib import messages
from django.shortcuts import redirect
from django.views import View
from django.views.generic import ListView
from core.exceptions import ConflictError, NotFoundError
from core.mixins import ApproverRequiredMixin
from .models import ApprovalRequest
from .services import ApprovalService


class ApprovalQueueView(ApproverRequiredMixin, ListView):
    template_name = "approvals/approval_queue.html"
    context_object_name = "requests"

    def get_queryset(self):
        status = self.request.GET.get("status", "pending")
        qs = ApprovalRequest.objects.select_related(
            "order", "order__user", "rule", "rule__template", "decided_by"
        ).prefetch_related("order__items", "order__items__template")
        if status == "all":
            return qs.all()
        return qs.filter(status=status)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_status"] = self.request.GET.get("status", "pending")
        return ctx


class ApprovalApproveView(ApproverRequiredMixin, View):
    def post(self, request, pk):
        try:
            ApprovalService.approve(pk, request.user)
            messages.success(request, "Genehmigung erteilt.")
        except (ConflictError, NotFoundError) as e:
            messages.error(request, e.message)
        return redirect("approvals:queue")


class ApprovalRejectView(ApproverRequiredMixin, View):
    def post(self, request, pk):
        comment = request.POST.get("comment", "")
        try:
            ApprovalService.reject(pk, request.user, comment=comment)
            messages.success(request, "Bestellung abgelehnt.")
        except (ConflictError, NotFoundError) as e:
            messages.error(request, e.message)
        return redirect("approvals:queue")
