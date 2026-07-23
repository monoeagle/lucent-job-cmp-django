"""Service layer for the approvals app."""
from django.db import transaction
from django.utils import timezone

from apps.accounts.services import AccountService
from apps.approvals.models import ApprovalRequest, ApprovalRule
from apps.notifications.services import NotificationService
from apps.orders.services import OrderService
from apps.orders.transitions import transition
from apps.provisioning.tasks import dispatch_provisioning
from core.domain.enums import UserRole
from core.domain.value_objects import OrderStatus, StatusMachine
from core.exceptions import ConflictError, ForbiddenError, NotFoundError


class ApprovalService:
    """Application service for approval operations."""

    @staticmethod
    def needs_approval(order_id):
        """Check if an order requires approval based on active rules."""
        order = OrderService.get_order(order_id)
        template_ids = order.items.values_list(
            "template_id", flat=True
        ).distinct()
        return ApprovalRule.objects.filter(
            template_id__in=template_ids, is_active=True
        ).exists()

    @staticmethod
    def create_approval_requests(order_id, actor):
        """Create pending approval requests for all matching rules."""
        order = OrderService.get_order(order_id)
        template_ids = order.items.values_list(
            "template_id", flat=True
        ).distinct()
        rules = ApprovalRule.objects.filter(
            template_id__in=template_ids, is_active=True
        )
        requests = []
        for rule in rules:
            req = ApprovalRequest.objects.create(
                order=order, rule=rule, status="pending"
            )
            requests.append(req)
        if requests:
            transition(order, OrderStatus.PENDING_APPROVAL, actor)
        return requests

    @staticmethod
    def _load_pending(request_id, approver):
        """Load a pending request and check the approver against its rule.

        `ApprovalRule.approver_role` names the role the decision requires.
        A lower role must not decide, no matter that the view-level mixin
        already let it through.
        """
        try:
            req = ApprovalRequest.objects.select_related("order", "rule").get(
                pk=request_id
            )
        except ApprovalRequest.DoesNotExist:
            raise NotFoundError(
                f"ApprovalRequest {request_id} not found."
            )
        if req.status != "pending":
            raise ConflictError(f"Request already decided: {req.status}")
        verlangt = req.rule.approver_role
        if verlangt not in UserRole.values:
            # Sonst haengt die Anfrage fuer immer: is_at_least_role liefert fuer
            # unbekannte Werte stumm False, auch fuer den Superadmin.
            raise ConflictError(
                f"Regel {req.rule_id} nennt die unbekannte Rolle '{verlangt}' — "
                "die Anfrage ist so von niemandem entscheidbar."
            )
        if not AccountService.is_at_least_role(approver.role, verlangt):
            raise ForbiddenError(
                f"Diese Entscheidung verlangt die Rolle '{verlangt}'."
            )
        return req

    @staticmethod
    def approve(request_id, approver):
        """Approve an approval request. Advances order if all approved."""
        req = ApprovalService._load_pending(request_id, approver)
        req.status = "approved"
        req.decided_by = approver
        req.decided_at = timezone.now()
        req.save()
        order = req.order
        all_reqs = ApprovalRequest.objects.filter(order=order)
        if (
            not all_reqs.filter(status="pending").exists()
            and not all_reqs.filter(status="rejected").exists()
        ):
            transition(order, OrderStatus.APPROVED, approver)
            transaction.on_commit(
                lambda: dispatch_provisioning.delay(order.pk)
            )
            NotificationService.create(
                order.user,
                "Bestellung genehmigt",
                f"Ihre Bestellung #{order.pk} wurde genehmigt und wird "
                "bereitgestellt.",
                category="success",
            )

    @staticmethod
    def reject(request_id, approver, comment=""):
        """Reject an approval request. Immediately rejects the order."""
        req = ApprovalService._load_pending(request_id, approver)
        req.status = "rejected"
        req.decided_by = approver
        req.decided_at = timezone.now()
        req.comment = comment
        req.save()
        transition(req.order, OrderStatus.REJECTED, approver, comment=comment)
        NotificationService.create(
            req.order.user,
            "Bestellung abgelehnt",
            f"Ihre Bestellung #{req.order.pk} wurde abgelehnt: {comment}",
            category="warning",
        )

    @staticmethod
    def list_pending_requests():
        """Return all pending approval requests."""
        return list(
            ApprovalRequest.objects.filter(status="pending").select_related(
                "order", "rule"
            )
        )
