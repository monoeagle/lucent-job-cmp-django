"""Views for the approvals app."""
from django.contrib import messages
from django.shortcuts import redirect
from django.views import View
from django.views.generic import ListView

from core.exceptions import ConflictError, NotFoundError
from core.mixins import ApproverRequiredMixin

from .services import ApprovalService


class ApprovalQueueView(ApproverRequiredMixin, ListView):
    """Display pending approval requests for approvers."""

    template_name = "approvals/approval_queue.html"
    context_object_name = "requests"

    def get_queryset(self):
        return ApprovalService.list_pending_requests()


class ApprovalApproveView(ApproverRequiredMixin, View):
    """Approve a pending approval request."""

    def post(self, request, pk):
        try:
            ApprovalService.approve(pk, request.user)
            messages.success(request, "Genehmigung erteilt.")
        except (ConflictError, NotFoundError) as e:
            messages.error(request, e.message)
        return redirect("approvals:queue")


class ApprovalRejectView(ApproverRequiredMixin, View):
    """Reject a pending approval request."""

    def post(self, request, pk):
        comment = request.POST.get("comment", "")
        try:
            ApprovalService.reject(pk, request.user, comment=comment)
            messages.success(request, "Bestellung abgelehnt.")
        except (ConflictError, NotFoundError) as e:
            messages.error(request, e.message)
        return redirect("approvals:queue")
