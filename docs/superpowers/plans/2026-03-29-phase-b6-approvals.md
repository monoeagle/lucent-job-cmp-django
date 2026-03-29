# Phase B6: Approval Workflow — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement rule-based approval workflow — ApprovalRules define when orders need approval, ApprovalRequests track pending decisions, ApprovalService handles approve/reject with order status transitions.

**Architecture:** `apps/approvals/` with models, services, views. ApprovalService checks rules on order submission, creates requests, handles approve/reject → triggers provisioning on approval.

**Tech Stack:** Django 6.0, pytest-django, factory_boy, HTMX for inline actions

---

## Task 1: Approval Models

**Files:**
- Create: `mpp/apps/approvals/__init__.py`, `apps.py`, `models.py`, `admin.py`
- Modify: `mpp/config/settings/base.py`
- Test: `tests/integration/test_approval_model.py`

Tests:
```python
import pytest
from apps.approvals.models import ApprovalRule, ApprovalRequest
from tests.factories import UserFactory, ServiceTemplateFactory, OrderFactory

@pytest.mark.django_db
class TestApprovalRule:
    def test_create_rule(self):
        t = ServiceTemplateFactory()
        rule = ApprovalRule.objects.create(
            template=t, condition={"min_cpu": 8}, approver_role="approver")
        assert rule.pk is not None

    def test_str(self):
        t = ServiceTemplateFactory(name="Linux VM")
        rule = ApprovalRule.objects.create(template=t, approver_role="approver")
        assert "Linux VM" in str(rule)

    def test_default_condition_empty(self):
        t = ServiceTemplateFactory()
        rule = ApprovalRule.objects.create(template=t, approver_role="approver")
        assert rule.condition == {}

@pytest.mark.django_db
class TestApprovalRequest:
    def test_create_request(self):
        t = ServiceTemplateFactory()
        rule = ApprovalRule.objects.create(template=t, approver_role="approver")
        order = OrderFactory()
        req = ApprovalRequest.objects.create(order=order, rule=rule, status="pending")
        assert req.pk is not None

    def test_approve(self):
        t = ServiceTemplateFactory()
        rule = ApprovalRule.objects.create(template=t, approver_role="approver")
        order = OrderFactory()
        approver = UserFactory()
        req = ApprovalRequest.objects.create(order=order, rule=rule, status="pending")
        req.status = "approved"
        req.decided_by = approver
        req.save()
        assert req.status == "approved"

    def test_str(self):
        t = ServiceTemplateFactory()
        rule = ApprovalRule.objects.create(template=t, approver_role="approver")
        order = OrderFactory()
        req = ApprovalRequest.objects.create(order=order, rule=rule, status="pending")
        assert "pending" in str(req).lower()
```

Models:
```python
from django.conf import settings
from django.db import models
from core.mixins import TimeStampedModel

class ApprovalRule(TimeStampedModel):
    template = models.ForeignKey("catalog.ServiceTemplate", on_delete=models.CASCADE, related_name="approval_rules")
    condition = models.JSONField(default=dict)
    approver_role = models.CharField(max_length=20, default="approver")
    is_active = models.BooleanField(default=True)
    class Meta:
        db_table = "approval_rules"
    def __str__(self):
        return f"Rule: {self.template.name} → {self.approver_role}"

class ApprovalRequest(TimeStampedModel):
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="approval_requests")
    rule = models.ForeignKey(ApprovalRule, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default="pending")
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    comment = models.TextField(blank=True, default="")
    class Meta:
        db_table = "approval_requests"
        ordering = ["-created_at"]
    def __str__(self):
        return f"Approval #{self.pk} ({self.status}) for Order #{self.order_id}"
```

---

## Task 2: ApprovalService

**Test** `tests/unit/test_approval_service.py`:
```python
import pytest
from apps.approvals.models import ApprovalRule, ApprovalRequest
from apps.approvals.services import ApprovalService
from apps.orders.models import Order
from core.domain.value_objects import OrderStatus
from core.exceptions import ConflictError, NotFoundError
from tests.factories import UserFactory, ServiceTemplateFactory, OrderFactory, OrderItemFactory

@pytest.mark.django_db
class TestApprovalServiceCheckRules:
    def test_no_rules_returns_false(self):
        order = OrderFactory(status=OrderStatus.SUBMITTED)
        OrderItemFactory(order=order)
        assert ApprovalService.needs_approval(order.pk) is False

    def test_matching_rule_returns_true(self):
        template = ServiceTemplateFactory()
        ApprovalRule.objects.create(template=template, approver_role="approver")
        order = OrderFactory(status=OrderStatus.SUBMITTED)
        OrderItemFactory(order=order, template=template)
        assert ApprovalService.needs_approval(order.pk) is True

    def test_inactive_rule_ignored(self):
        template = ServiceTemplateFactory()
        ApprovalRule.objects.create(template=template, approver_role="approver", is_active=False)
        order = OrderFactory(status=OrderStatus.SUBMITTED)
        OrderItemFactory(order=order, template=template)
        assert ApprovalService.needs_approval(order.pk) is False

@pytest.mark.django_db
class TestApprovalServiceCreate:
    def test_create_approval_request(self):
        template = ServiceTemplateFactory()
        rule = ApprovalRule.objects.create(template=template, approver_role="approver")
        order = OrderFactory(status=OrderStatus.SUBMITTED)
        OrderItemFactory(order=order, template=template)
        requests = ApprovalService.create_approval_requests(order.pk)
        assert len(requests) == 1
        assert requests[0].status == "pending"
        order.refresh_from_db()
        assert order.status == OrderStatus.PENDING_APPROVAL

@pytest.mark.django_db
class TestApprovalServiceDecide:
    def test_approve_order(self):
        template = ServiceTemplateFactory()
        rule = ApprovalRule.objects.create(template=template, approver_role="approver")
        order = OrderFactory(status=OrderStatus.PENDING_APPROVAL)
        OrderItemFactory(order=order, template=template)
        req = ApprovalRequest.objects.create(order=order, rule=rule, status="pending")
        approver = UserFactory(role="approver")
        ApprovalService.approve(req.pk, approver)
        req.refresh_from_db()
        assert req.status == "approved"
        order.refresh_from_db()
        assert order.status == OrderStatus.APPROVED

    def test_reject_order(self):
        template = ServiceTemplateFactory()
        rule = ApprovalRule.objects.create(template=template, approver_role="approver")
        order = OrderFactory(status=OrderStatus.PENDING_APPROVAL)
        req = ApprovalRequest.objects.create(order=order, rule=rule, status="pending")
        approver = UserFactory(role="approver")
        ApprovalService.reject(req.pk, approver, comment="Not needed")
        req.refresh_from_db()
        assert req.status == "rejected"
        order.refresh_from_db()
        assert order.status == OrderStatus.REJECTED

    def test_approve_already_decided_raises(self):
        template = ServiceTemplateFactory()
        rule = ApprovalRule.objects.create(template=template, approver_role="approver")
        order = OrderFactory(status=OrderStatus.PENDING_APPROVAL)
        req = ApprovalRequest.objects.create(order=order, rule=rule, status="approved")
        approver = UserFactory(role="approver")
        with pytest.raises(ConflictError):
            ApprovalService.approve(req.pk, approver)

    def test_list_pending_requests(self):
        template = ServiceTemplateFactory()
        rule = ApprovalRule.objects.create(template=template, approver_role="approver")
        order = OrderFactory(status=OrderStatus.PENDING_APPROVAL)
        ApprovalRequest.objects.create(order=order, rule=rule, status="pending")
        ApprovalRequest.objects.create(order=order, rule=rule, status="approved")
        pending = ApprovalService.list_pending_requests()
        assert len(pending) == 1
```

Service:
```python
from django.utils import timezone
from apps.approvals.models import ApprovalRule, ApprovalRequest
from apps.orders.services import OrderService
from core.domain.value_objects import OrderStatus, StatusMachine
from core.exceptions import ConflictError, NotFoundError

class ApprovalService:
    @staticmethod
    def needs_approval(order_id):
        order = OrderService.get_order(order_id)
        template_ids = order.items.values_list("template_id", flat=True).distinct()
        return ApprovalRule.objects.filter(template_id__in=template_ids, is_active=True).exists()

    @staticmethod
    def create_approval_requests(order_id):
        order = OrderService.get_order(order_id)
        template_ids = order.items.values_list("template_id", flat=True).distinct()
        rules = ApprovalRule.objects.filter(template_id__in=template_ids, is_active=True)
        requests = []
        for rule in rules:
            req = ApprovalRequest.objects.create(order=order, rule=rule, status="pending")
            requests.append(req)
        if requests:
            StatusMachine.validate_transition(order.status, OrderStatus.PENDING_APPROVAL)
            order.status = OrderStatus.PENDING_APPROVAL
            order.save()
        return requests

    @staticmethod
    def approve(request_id, approver):
        try:
            req = ApprovalRequest.objects.select_related("order").get(pk=request_id)
        except ApprovalRequest.DoesNotExist:
            raise NotFoundError(f"ApprovalRequest {request_id} not found.")
        if req.status != "pending":
            raise ConflictError(f"Request already decided: {req.status}")
        req.status = "approved"
        req.decided_by = approver
        req.decided_at = timezone.now()
        req.save()
        order = req.order
        all_reqs = ApprovalRequest.objects.filter(order=order)
        if not all_reqs.filter(status="pending").exists():
            if not all_reqs.filter(status="rejected").exists():
                order.status = OrderStatus.APPROVED
                order.save()

    @staticmethod
    def reject(request_id, approver, comment=""):
        try:
            req = ApprovalRequest.objects.select_related("order").get(pk=request_id)
        except ApprovalRequest.DoesNotExist:
            raise NotFoundError(f"ApprovalRequest {request_id} not found.")
        if req.status != "pending":
            raise ConflictError(f"Request already decided: {req.status}")
        req.status = "rejected"
        req.decided_by = approver
        req.decided_at = timezone.now()
        req.comment = comment
        req.save()
        order = req.order
        order.status = OrderStatus.REJECTED
        order.save()

    @staticmethod
    def list_pending_requests():
        return list(ApprovalRequest.objects.filter(status="pending").select_related("order", "rule"))
```

---

## Task 3: Approval Views & Templates

**Test** `tests/integration/test_approval_views.py`:
```python
import pytest
from django.urls import reverse
from apps.approvals.models import ApprovalRule, ApprovalRequest
from core.domain.enums import UserRole
from core.domain.value_objects import OrderStatus
from tests.factories import UserFactory, ServiceTemplateFactory, OrderFactory, OrderItemFactory

@pytest.mark.django_db
class TestApprovalQueueView:
    def test_requires_login(self, client):
        response = client.get(reverse("approvals:queue"))
        assert response.status_code == 302

    def test_requester_forbidden(self, client):
        user = UserFactory(role=UserRole.REQUESTER)
        client.force_login(user)
        response = client.get(reverse("approvals:queue"))
        assert response.status_code == 403

    def test_approver_can_access(self, client):
        user = UserFactory(role=UserRole.APPROVER)
        client.force_login(user)
        response = client.get(reverse("approvals:queue"))
        assert response.status_code == 200

    def test_shows_pending_requests(self, client):
        template = ServiceTemplateFactory()
        rule = ApprovalRule.objects.create(template=template, approver_role="approver")
        order = OrderFactory(status=OrderStatus.PENDING_APPROVAL)
        ApprovalRequest.objects.create(order=order, rule=rule, status="pending")
        user = UserFactory(role=UserRole.APPROVER)
        client.force_login(user)
        response = client.get(reverse("approvals:queue"))
        assert response.status_code == 200

@pytest.mark.django_db
class TestApprovalActionViews:
    def test_approve(self, client):
        template = ServiceTemplateFactory()
        rule = ApprovalRule.objects.create(template=template, approver_role="approver")
        order = OrderFactory(status=OrderStatus.PENDING_APPROVAL)
        req = ApprovalRequest.objects.create(order=order, rule=rule, status="pending")
        user = UserFactory(role=UserRole.APPROVER)
        client.force_login(user)
        response = client.post(reverse("approvals:approve", kwargs={"pk": req.pk}))
        assert response.status_code == 302
        req.refresh_from_db()
        assert req.status == "approved"

    def test_reject(self, client):
        template = ServiceTemplateFactory()
        rule = ApprovalRule.objects.create(template=template, approver_role="approver")
        order = OrderFactory(status=OrderStatus.PENDING_APPROVAL)
        req = ApprovalRequest.objects.create(order=order, rule=rule, status="pending")
        user = UserFactory(role=UserRole.APPROVER)
        client.force_login(user)
        response = client.post(
            reverse("approvals:reject", kwargs={"pk": req.pk}),
            {"comment": "Not approved"})
        assert response.status_code == 302
        req.refresh_from_db()
        assert req.status == "rejected"
```

Views:
```python
from django.contrib import messages
from django.shortcuts import redirect
from django.views import View
from django.views.generic import ListView
from core.exceptions import ConflictError, NotFoundError
from core.mixins import ApproverRequiredMixin
from .services import ApprovalService

class ApprovalQueueView(ApproverRequiredMixin, ListView):
    template_name = "approvals/approval_queue.html"
    context_object_name = "requests"
    def get_queryset(self):
        return ApprovalService.list_pending_requests()

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
```

URLs, templates (approval_queue.html with DaisyUI table + approve/reject buttons).

---

## Summary

| Task | Description | Tests |
|------|-------------|-------|
| 1 | ApprovalRule + ApprovalRequest models | 6 |
| 2 | ApprovalService | 8 |
| 3 | Approval views + templates | 6 |
| **Total new** | | **~20** |
| **Running total** | | **~201** |
