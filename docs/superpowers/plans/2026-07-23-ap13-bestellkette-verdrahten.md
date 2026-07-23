# AP-13 — Bestellkette verdrahten Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die sechs fehlenden Aufrufe der Bestellkette verdrahten, jeden Order-Statuswechsel über einen zentralen `transition()` leiten (der zugleich das Audit-Log füllt) und die Kette per E2E-Test durch die Views absichern.

**Architecture:** Neuer Orchestrator `apps/orders/transitions.py::transition(order, to_status, actor, **details)` = einziger erlaubter Ort für `order.status = …`; er prüft via `StatusMachine` (bleibt rein in `core/domain`), setzt+speichert den Status und schreibt `AuditService.log`. Benachrichtigungen bleiben am Aufrufort in den Services. Ein AST-Wächter-Test verbietet direkte `order.status`-Zuweisungen außerhalb `transitions.py`.

**Tech Stack:** Django 6.0, pytest-django 4.12, factory_boy, Celery (`CELERY_TASK_ALWAYS_EAGER=True` in Tests), PostgreSQL.

## Global Constraints

- **TDD ist Pflicht** — je Lücke zuerst ein roter Test; Wächter-Test per Fehlerinjektion belegen.
- **Thin Views** — Logik in Services, nicht in Views.
- **Architekturregel `core/ → apps/` (nicht umgekehrt)** — deshalb wohnt `transition()` in `apps/orders/`, NICHT in `core/domain/`. `StatusMachine` bleibt rein in `core/domain/value_objects.py`.
- **`order.status = …` nur in `apps/orders/transitions.py`** — überall sonst über `transition()`.
- **`transaction.on_commit`** für den Celery-Start — sonst läuft der Task vor dem Commit.
- **Tests laufen vom Repo-Root** mit `venv/bin/python3 -m pytest …` (pytest.ini: `pythonpath = cmp`, `testpaths = tests`, Settings `config.settings.testing`).
- **Django-`client`-Fixture für View-/E2E-Tests** — das ist das etablierte Muster hier (nicht RequestFactory).
- **Deutsch** für Benachrichtigungstexte und Commit-Bodies-Prosa; Commit-Betreff auf Englisch im `feat:`/`test:`-Stil wie im Repo.
- Jeder Commit endet mit `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

## Datei-Übersicht

| Datei | Rolle | Aktion |
|---|---|---|
| `cmp/apps/orders/transitions.py` | zentraler Übergang + Audit | **neu** |
| `cmp/apps/accounts/services.py` | Rollen-Helfer für Genehmiger-Empfänger | ändern |
| `cmp/apps/approvals/services.py` | create_requests(actor), approve→dispatch+notify, reject→notify | ändern |
| `cmp/apps/orders/services.py` | submit_order(actor) + Approval-Branch + Genehmiger-Notify | ändern |
| `cmp/apps/provisioning/services.py` | dispatch/complete über transition; DONE→Subscription+Notify | ändern |
| `cmp/apps/provisioning/tasks.py` | Stub schließt sofort ab | ändern |
| `cmp/apps/orders/views.py` | actor an submit_order durchreichen | ändern |
| `tests/unit/test_transitions.py` | Übergang + Audit | **neu** |
| `tests/unit/test_no_direct_status.py` | Wächter-Test (AST) | **neu** |
| `tests/e2e/test_workflow_through_views.py` | DoD-E2E durch die Views | **neu** |
| `tests/unit/test_account_service.py`, `test_approval_service.py`, `test_order_service.py`, `test_provisioning_service.py` | neue + angepasste Tests | ändern |
| `tests/integration/test_order_views.py`, `tests/e2e/test_order_workflow.py` | an verdrahtetes Verhalten anpassen | ändern |

---

## Task 1: `transition()` — zentraler Übergang mit Audit

**Files:**
- Create: `cmp/apps/orders/transitions.py`
- Test: `tests/unit/test_transitions.py`

**Interfaces:**
- Consumes: `StatusMachine.validate_transition` (`core/domain/value_objects.py`), `AuditService.log(user, action, resource_type, resource_id, details=None, ip_address=None)` (`apps/audit/services.py`).
- Produces: `transition(order, to_status, actor, **details) -> None` — validiert, setzt `order.status = to_status`, `order.save()`, schreibt `AuditLog(action=f"order.<to_status>", resource_type="order", resource_id=order.pk, details={"from": <alt>, **details}, user=actor)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_transitions.py
"""Test the central order transition helper."""
import pytest
from apps.audit.models import AuditLog
from apps.orders.transitions import transition
from core.domain.value_objects import OrderStatus
from tests.factories import UserFactory, OrderFactory


@pytest.mark.django_db
class TestTransition:
    def test_sets_status_and_saves(self):
        actor = UserFactory()
        order = OrderFactory(status=OrderStatus.DRAFT)
        transition(order, OrderStatus.VALIDATED, actor)
        order.refresh_from_db()
        assert order.status == OrderStatus.VALIDATED

    def test_writes_audit_log_with_from_and_action(self):
        actor = UserFactory()
        order = OrderFactory(status=OrderStatus.DRAFT)
        transition(order, OrderStatus.VALIDATED, actor)
        log = AuditLog.objects.get(resource_type="order", resource_id=order.pk)
        assert log.action == "order.validated"
        assert log.user == actor
        assert log.details["from"] == "draft"

    def test_merges_extra_details(self):
        actor = UserFactory()
        order = OrderFactory(status=OrderStatus.SUBMITTED)
        transition(order, OrderStatus.REJECTED, actor, comment="zu teuer")
        log = AuditLog.objects.get(resource_type="order", resource_id=order.pk)
        assert log.details["comment"] == "zu teuer"
        assert log.details["from"] == "submitted"

    def test_rejects_invalid_transition(self):
        actor = UserFactory()
        order = OrderFactory(status=OrderStatus.DRAFT)
        with pytest.raises(ValueError):
            transition(order, OrderStatus.DONE, actor)

    def test_actor_may_be_none(self):
        order = OrderFactory(status=OrderStatus.APPROVED)
        transition(order, OrderStatus.PROVISIONING, None)
        log = AuditLog.objects.get(resource_type="order", resource_id=order.pk)
        assert log.user is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/python3 -m pytest tests/unit/test_transitions.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'apps.orders.transitions'`

- [ ] **Step 3: Write minimal implementation**

```python
# cmp/apps/orders/transitions.py
"""Zentraler Order-Statuswechsel — der einzige erlaubte Ort fuer order.status = ...

Buendelt Uebergangspruefung (StatusMachine), Statuswechsel und Audit-Log.
Bewusst OHNE Benachrichtigungen: deren Empfaenger/Text sind je Uebergang
verschieden und bleiben am jeweiligen Aufrufort in den Services.

Wohnt in apps/orders/ (nicht core/domain/), weil er AuditService aus apps/
aufruft und core nicht auf apps zeigen darf.
"""
from apps.audit.services import AuditService
from core.domain.value_objects import StatusMachine


def transition(order, to_status, actor, **details):
    """Validate + apply a status change and record it in the audit log."""
    from_status = str(order.status)
    StatusMachine.validate_transition(order.status, to_status)
    order.status = to_status
    order.save()
    action = f"order.{getattr(to_status, 'value', to_status)}"
    AuditService.log(
        actor,
        action,
        "order",
        order.pk,
        details={"from": from_status, **details},
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `venv/bin/python3 -m pytest tests/unit/test_transitions.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add cmp/apps/orders/transitions.py tests/unit/test_transitions.py
git commit -m "feat: AP-13 zentraler order transition() mit Audit-Log

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: `AccountService.list_users_with_min_role`

**Files:**
- Modify: `cmp/apps/accounts/services.py`
- Test: `tests/unit/test_account_service.py`

**Interfaces:**
- Consumes: `ROLE_HIERARCHY`, `User` model.
- Produces: `AccountService.list_users_with_min_role(minimum_role) -> list[User]` — aktive User mit Rolle ≥ `minimum_role`; `[]` bei unbekannter Rolle.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_account_service.py  — anhaengen
@pytest.mark.django_db
class TestListUsersWithMinRole:
    def test_returns_users_at_or_above_role(self):
        from apps.accounts.services import AccountService
        from tests.factories import UserFactory
        UserFactory(role="requester")
        appr = UserFactory(role="approver")
        admin = UserFactory(role="admin")
        result = AccountService.list_users_with_min_role("approver")
        pks = {u.pk for u in result}
        assert appr.pk in pks
        assert admin.pk in pks
        assert len(result) == 2

    def test_unknown_role_returns_empty(self):
        from apps.accounts.services import AccountService
        assert AccountService.list_users_with_min_role("bogus") == []

    def test_excludes_inactive_users(self):
        from apps.accounts.services import AccountService
        from tests.factories import UserFactory
        UserFactory(role="approver", is_active=False)
        assert AccountService.list_users_with_min_role("approver") == []
```

Sicherstellen, dass die Datei oben `import pytest` hat (falls nicht, ergänzen).

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/python3 -m pytest tests/unit/test_account_service.py::TestListUsersWithMinRole -v`
Expected: FAIL — `AttributeError: type object 'AccountService' has no attribute 'list_users_with_min_role'`

- [ ] **Step 3: Write minimal implementation**

Am Ende der Klasse `AccountService` in `cmp/apps/accounts/services.py` anfügen:

```python
    @staticmethod
    def list_users_with_min_role(minimum_role):
        """Return active users whose role is at or above minimum_role."""
        try:
            min_level = ROLE_HIERARCHY.index(minimum_role)
        except ValueError:
            return []
        eligible = ROLE_HIERARCHY[min_level:]
        return list(User.objects.filter(role__in=eligible, is_active=True))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `venv/bin/python3 -m pytest tests/unit/test_account_service.py::TestListUsersWithMinRole -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add cmp/apps/accounts/services.py tests/unit/test_account_service.py
git commit -m "feat: AP-13 AccountService.list_users_with_min_role

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: ApprovalService verdrahten (Lücken 2, 5, 6)

**Files:**
- Modify: `cmp/apps/approvals/services.py`
- Test: `tests/unit/test_approval_service.py`

**Interfaces:**
- Consumes: `transition` (Task 1), `dispatch_provisioning.delay` (`apps/provisioning/tasks.py`), `NotificationService.create`, `transaction.on_commit`.
- Produces:
  - `ApprovalService.create_approval_requests(order_id, actor) -> list` — **Signatur um `actor` erweitert**; Übergang nach `PENDING_APPROVAL` via `transition()`.
  - `ApprovalService.approve(request_id, approver)` — bei allen genehmigt: `transition(→APPROVED)` + `on_commit(dispatch_provisioning.delay)` + Besteller-Notify.
  - `ApprovalService.reject(request_id, approver, comment="")` — `transition(→REJECTED, comment=…)` + Besteller-Notify.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_approval_service.py  — anhaengen (import pytest oben ist vorhanden)
@pytest.mark.django_db
class TestApprovalWiring:
    def _order_with_rule(self):
        from apps.orders.models import Order, OrderItem
        from apps.approvals.models import ApprovalRule
        from tests.factories import UserFactory, ServiceTemplateFactory, OrderFactory, OrderItemFactory
        from core.domain.value_objects import OrderStatus
        requester = UserFactory(role="requester")
        template = ServiceTemplateFactory()
        ApprovalRule.objects.create(template=template, approver_role="approver")
        order = OrderFactory(user=requester, status=OrderStatus.SUBMITTED)
        OrderItemFactory(order=order, template=template)
        return order, requester

    def test_create_requests_takes_actor_and_audits(self):
        from apps.approvals.services import ApprovalService
        from apps.audit.models import AuditLog
        from core.domain.value_objects import OrderStatus
        order, requester = self._order_with_rule()
        reqs = ApprovalService.create_approval_requests(order.pk, requester)
        assert len(reqs) == 1
        order.refresh_from_db()
        assert order.status == OrderStatus.PENDING_APPROVAL
        assert AuditLog.objects.filter(
            resource_type="order", resource_id=order.pk, action="order.pending_approval"
        ).exists()

    def test_approve_triggers_dispatch_on_commit(self, django_capture_on_commit_callbacks):
        from apps.approvals.services import ApprovalService
        from apps.provisioning.models import DispatchLog
        from tests.factories import UserFactory
        order, requester = self._order_with_rule()
        approver = UserFactory(role="approver")
        reqs = ApprovalService.create_approval_requests(order.pk, requester)
        with django_capture_on_commit_callbacks(execute=True):
            ApprovalService.approve(reqs[0].pk, approver)
        order.refresh_from_db()
        # dispatch lief -> Provisioning-Log existiert
        assert DispatchLog.objects.filter(order_item__order=order).exists()

    def test_approve_notifies_requester(self):
        from apps.approvals.services import ApprovalService
        from apps.notifications.models import Notification
        from tests.factories import UserFactory
        order, requester = self._order_with_rule()
        approver = UserFactory(role="approver")
        reqs = ApprovalService.create_approval_requests(order.pk, requester)
        ApprovalService.approve(reqs[0].pk, approver)
        assert Notification.objects.filter(user=requester, title="Bestellung genehmigt").exists()

    def test_reject_notifies_requester_and_audits(self):
        from apps.approvals.services import ApprovalService
        from apps.notifications.models import Notification
        from apps.audit.models import AuditLog
        from tests.factories import UserFactory
        order, requester = self._order_with_rule()
        approver = UserFactory(role="approver")
        reqs = ApprovalService.create_approval_requests(order.pk, requester)
        ApprovalService.reject(reqs[0].pk, approver, comment="zu teuer")
        assert Notification.objects.filter(user=requester, title="Bestellung abgelehnt").exists()
        assert AuditLog.objects.filter(
            resource_type="order", resource_id=order.pk, action="order.rejected"
        ).exists()
```

Außerdem den bestehenden Test `test_create_approval_request` (Klasse weiter oben) auf die neue Signatur anpassen: `ApprovalService.create_approval_requests(order.pk, approver)` — dazu im Setup einen `approver`/`user` bereitstellen (z. B. `order.user`). Der bestehende `test_approve_order` / `test_reject_order` bleiben inhaltlich gültig (ohne `on_commit`-Capture feuert der Dispatch nicht → Order bleibt `APPROVED`).

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/python3 -m pytest tests/unit/test_approval_service.py -v`
Expected: FAIL — `TypeError: create_approval_requests() missing 1 required positional argument: 'actor'` (neue Tests) bzw. fehlende Dispatch/Notification.

- [ ] **Step 3: Write minimal implementation**

In `cmp/apps/approvals/services.py` die Importe oben ergänzen und die drei Methoden ersetzen:

```python
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
```

```python
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
```

```python
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
```

Hinweis: Der Import `from apps.provisioning.tasks import dispatch_provisioning` ist zyklusfrei — `provisioning.services` importiert nie `approvals`.

- [ ] **Step 4: Run test to verify it passes**

Run: `venv/bin/python3 -m pytest tests/unit/test_approval_service.py -v`
Expected: PASS (alle, inkl. angepasstem `test_create_approval_request`)

- [ ] **Step 5: Commit**

```bash
git add cmp/apps/approvals/services.py tests/unit/test_approval_service.py
git commit -m "feat: AP-13 ApprovalService verdrahtet (dispatch on_commit, Notify, Audit)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: OrderService.submit_order verdrahten (Lücken 1, 5, 6-Genehmiger)

**Files:**
- Modify: `cmp/apps/orders/services.py`
- Test: `tests/unit/test_order_service.py`

**Interfaces:**
- Consumes: `transition` (Task 1), `AccountService.list_users_with_min_role` (Task 2), `ApprovalService.needs_approval` / `.create_approval_requests(order_id, actor)` (Task 3, **lazy import** wegen orders↔approvals-Zyklus), `NotificationService.create`.
- Produces: `OrderService.submit_order(order_id, actor)` — **Signatur um `actor` erweitert**; DRAFT→VALIDATED→SUBMITTED via `transition()`; bei Regel: `create_approval_requests` + Genehmiger-Notify; sonst `transition(SUBMITTED→APPROVED)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_order_service.py  — anhaengen
@pytest.mark.django_db
class TestOrderServiceSubmitWiring:
    def test_submit_without_rule_auto_approves(self):
        from apps.audit.models import AuditLog
        user = UserFactory(role="requester")
        template = ServiceTemplateFactory()
        order = OrderFactory(user=user)
        OrderItemFactory(order=order, template=template)
        result = OrderService.submit_order(order_id=order.pk, actor=user)
        assert result.status == OrderStatus.APPROVED
        assert AuditLog.objects.filter(
            resource_type="order", resource_id=order.pk, action="order.approved"
        ).exists()

    def test_submit_with_rule_goes_pending_and_notifies_approvers(self):
        from apps.approvals.models import ApprovalRule, ApprovalRequest
        from apps.notifications.models import Notification
        user = UserFactory(role="requester")
        approver = UserFactory(role="approver")
        template = ServiceTemplateFactory()
        ApprovalRule.objects.create(template=template, approver_role="approver")
        order = OrderFactory(user=user)
        OrderItemFactory(order=order, template=template)
        OrderService.submit_order(order_id=order.pk, actor=user)
        order.refresh_from_db()
        assert order.status == OrderStatus.PENDING_APPROVAL
        assert ApprovalRequest.objects.filter(order=order).count() == 1
        assert Notification.objects.filter(
            user=approver, title="Neue Genehmigung erforderlich"
        ).exists()
```

Den bestehenden `test_submit_order_with_items` (Klasse `TestOrderServiceSubmit`) anpassen: Aufruf `OrderService.submit_order(order_id=order.pk, actor=order.user)` und Erwartung `OrderStatus.APPROVED` statt `SUBMITTED` (Order ohne Regel wird auto-genehmigt). `test_submit_empty_order_raises` / `test_submit_non_draft_raises` brauchen nur den `actor`-Parameter ergänzt.

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/python3 -m pytest tests/unit/test_order_service.py -v`
Expected: FAIL — `TypeError: submit_order() missing 1 required positional argument: 'actor'` bzw. Status `submitted != approved`.

- [ ] **Step 3: Write minimal implementation**

In `cmp/apps/orders/services.py` die Importe oben ergänzen …

```python
from apps.accounts.services import AccountService
from apps.catalog.services import CatalogService
from apps.notifications.services import NotificationService
from apps.orders.models import Order, OrderItem
from apps.orders.transitions import transition
from core.domain.enums import UserRole
from core.domain.value_objects import OrderStatus, StatusMachine
from core.exceptions import ConflictError, NotFoundError, ValidationError
```

… und `submit_order` ersetzen sowie `_notify_approvers` ergänzen:

```python
    @staticmethod
    def submit_order(order_id, actor):
        """Submit a draft order and route it into the approval workflow."""
        # lazy: bricht den orders<->approvals-Importzyklus
        from apps.approvals.services import ApprovalService

        order = OrderService.get_order(order_id)
        if order.status != OrderStatus.DRAFT:
            raise ConflictError(
                f"Cannot submit order in status '{order.status}'."
            )
        if order.items.count() == 0:
            raise ValidationError("Cannot submit an order without items.")
        transition(order, OrderStatus.VALIDATED, actor)
        transition(order, OrderStatus.SUBMITTED, actor)
        if ApprovalService.needs_approval(order.pk):
            requests = ApprovalService.create_approval_requests(order.pk, actor)
            OrderService._notify_approvers(order, requests)
        else:
            transition(order, OrderStatus.APPROVED, actor)
        return order

    @staticmethod
    def _notify_approvers(order, requests):
        """Notify every user eligible to decide one of the created requests."""
        empfaenger = {}
        for role in {req.rule.approver_role for req in requests}:
            for user in AccountService.list_users_with_min_role(role):
                empfaenger[user.pk] = user
        for user in empfaenger.values():
            NotificationService.create(
                user,
                "Neue Genehmigung erforderlich",
                f"Bestellung #{order.pk} wartet auf Ihre Genehmigung.",
                category="info",
            )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `venv/bin/python3 -m pytest tests/unit/test_order_service.py -v`
Expected: PASS (alle, inkl. angepasster Submit-Tests)

- [ ] **Step 5: Commit**

```bash
git add cmp/apps/orders/services.py tests/unit/test_order_service.py
git commit -m "feat: AP-13 submit_order verdrahtet (Approval-Branch, Auto-Approve, Notify)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: ProvisioningService + Task verdrahten (Lücken 3, 4, 5, 6-Besteller)

**Files:**
- Modify: `cmp/apps/provisioning/services.py`, `cmp/apps/provisioning/tasks.py`
- Test: `tests/unit/test_provisioning_service.py`

**Interfaces:**
- Consumes: `transition` (Task 1), `SubscriptionService.create_from_order`, `NotificationService.create`.
- Produces:
  - `dispatch_order`/`complete_dispatch` setzen Order-Status nur noch via `transition(…, None)`.
  - `complete_dispatch` bei `DONE` → `SubscriptionService.create_from_order` + Besteller-Notify (success); bei `FAILED` → Besteller-Notify (error).
  - `dispatch_provisioning`-Task schließt die laufenden DispatchLogs sofort ab (Stub — AP-20 ersetzt das durch Polling).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_provisioning_service.py  — anhaengen
@pytest.mark.django_db
class TestProvisioningWiring:
    def _approved_order(self):
        from tests.factories import UserFactory, ServiceTemplateFactory, OrderFactory, OrderItemFactory
        from core.domain.value_objects import OrderStatus
        user = UserFactory(role="requester")
        template = ServiceTemplateFactory()
        order = OrderFactory(user=user, status=OrderStatus.APPROVED)
        OrderItemFactory(order=order, template=template)
        return order, user

    def test_complete_done_creates_subscription_and_notifies(self):
        from apps.provisioning.services import ProvisioningService
        from apps.provisioning.models import DispatchLog
        from apps.subscriptions.models import Subscription
        from apps.notifications.models import Notification
        from core.domain.value_objects import OrderStatus
        order, user = self._approved_order()
        ProvisioningService.dispatch_order(order.pk)
        log = DispatchLog.objects.get(order_item__order=order)
        ProvisioningService.complete_dispatch(log.pk, success=True)
        order.refresh_from_db()
        assert order.status == OrderStatus.DONE
        assert Subscription.objects.filter(user=user).exists()
        assert Notification.objects.filter(user=user, title="Bestellung abgeschlossen").exists()

    def test_complete_failed_notifies_error(self):
        from apps.provisioning.services import ProvisioningService
        from apps.provisioning.models import DispatchLog
        from apps.notifications.models import Notification
        from core.domain.value_objects import OrderStatus
        order, user = self._approved_order()
        ProvisioningService.dispatch_order(order.pk)
        log = DispatchLog.objects.get(order_item__order=order)
        ProvisioningService.complete_dispatch(log.pk, success=False)
        order.refresh_from_db()
        assert order.status == OrderStatus.FAILED
        assert Notification.objects.filter(user=user, title="Bereitstellung fehlgeschlagen").exists()

    def test_dispatch_task_completes_chain(self):
        from apps.provisioning.tasks import dispatch_provisioning
        from core.domain.value_objects import OrderStatus
        order, user = self._approved_order()
        dispatch_provisioning(order.pk)   # eager: dispatch + sofort abschliessen
        order.refresh_from_db()
        assert order.status == OrderStatus.DONE
```

Die bestehenden `test_all_done_completes_order` / `test_any_failed_fails_order` bleiben gültig (Status-Assertions unverändert) — falls ihr Setup keine `OrderItem`s anlegt, ist das für `create_from_order` unkritisch (0 Subscriptions, kein Fehler).

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/python3 -m pytest tests/unit/test_provisioning_service.py::TestProvisioningWiring -v`
Expected: FAIL — keine Subscription/Notification; `dispatch_provisioning` schließt nicht ab.

- [ ] **Step 3: Write minimal implementation**

In `cmp/apps/provisioning/services.py` Importe ergänzen und die Statuswechsel + DONE/FAILED-Zweige ersetzen:

```python
from apps.notifications.services import NotificationService
from apps.orders.services import OrderService
from apps.orders.transitions import transition
from apps.provisioning.clients import GitLabStubClient
from apps.provisioning.models import DispatchLog
from apps.subscriptions.services import SubscriptionService
from core.domain.value_objects import OrderStatus, StatusMachine
from core.exceptions import ConflictError, NotFoundError
```

In `dispatch_order` den Block `StatusMachine.validate_transition(...); order.status = OrderStatus.PROVISIONING; order.save()` ersetzen durch:

```python
        transition(order, OrderStatus.PROVISIONING, None)
```

In `complete_dispatch` den Abschluss-Block ersetzen (die `log.status = …`-Zeilen für den DispatchLog bleiben — das ist NICHT `order.status`):

```python
        order = log.order_item.order
        all_logs = DispatchLog.objects.filter(order_item__order=order)

        if all_logs.filter(status="running").exists():
            return

        if all_logs.filter(status="failed").exists():
            transition(order, OrderStatus.FAILED, None)
            NotificationService.create(
                order.user,
                "Bereitstellung fehlgeschlagen",
                f"Die Bereitstellung Ihrer Bestellung #{order.pk} ist "
                "fehlgeschlagen.",
                category="error",
            )
        else:
            transition(order, OrderStatus.DONE, None)
            SubscriptionService.create_from_order(order.pk)
            NotificationService.create(
                order.user,
                "Bestellung abgeschlossen",
                f"Ihre Bestellung #{order.pk} wurde erfolgreich bereitgestellt.",
                category="success",
            )
```

In `cmp/apps/provisioning/tasks.py` den Stub-Abschluss ergänzen:

```python
"""Celery tasks for provisioning operations."""
from celery import shared_task

from .services import ProvisioningService


@shared_task
def dispatch_provisioning(order_id):
    """Dispatch all items of an approved order and (Stub) complete them at once."""
    ProvisioningService.dispatch_order(order_id)
    # Stub: keine echte Pipeline -> Rueckmeldung sofort simulieren.
    # AP-20 ersetzt das durch echtes Polling (complete_provisioning).
    from apps.provisioning.models import DispatchLog

    for log in DispatchLog.objects.filter(
        order_item__order_id=order_id, status="running"
    ):
        ProvisioningService.complete_dispatch(log.pk, success=True)


@shared_task
def complete_provisioning(dispatch_log_id, success=True):
    """Mark a dispatch as complete."""
    ProvisioningService.complete_dispatch(dispatch_log_id, success=success)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `venv/bin/python3 -m pytest tests/unit/test_provisioning_service.py -v`
Expected: PASS (alle)

- [ ] **Step 5: Commit**

```bash
git add cmp/apps/provisioning/services.py cmp/apps/provisioning/tasks.py tests/unit/test_provisioning_service.py
git commit -m "feat: AP-13 Provisioning verdrahtet (transition, Subscription, Notify, Stub-Abschluss)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Views — actor durchreichen + Integrationstests anpassen (Lücke 5 an der Oberfläche)

**Files:**
- Modify: `cmp/apps/orders/views.py`
- Test: `tests/integration/test_order_views.py`

**Interfaces:**
- Consumes: `OrderService.submit_order(order_id, actor)` (Task 4).
- Produces: `OrderSubmitView.post` reicht `request.user` als `actor` durch. Approve/Reject-Views bleiben unverändert (`request.user` als approver ist bereits gesetzt).

- [ ] **Step 1: Write the failing test**

Bestehenden `TestOrderSubmitView.test_submit_order` (`tests/integration/test_order_views.py`) auf das verdrahtete Verhalten anpassen — eine Bestellung ohne Regel wird über den View auto-genehmigt (der `on_commit`-Dispatch feuert im nicht-transaktionalen Test NICHT, Order bleibt `APPROVED`):

```python
    def test_submit_order(self, client):
        user = UserFactory()
        order = OrderFactory(user=user)
        OrderItemFactory(order=order)
        client.force_login(user)
        response = client.post(reverse("orders:submit", kwargs={"pk": order.pk}))
        assert response.status_code == 302
        order.refresh_from_db()
        assert order.status == OrderStatus.APPROVED
```

`test_submit_empty_order_stays_draft` bleibt unverändert (leer → `ValidationError` im View abgefangen → DRAFT).

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/python3 -m pytest tests/integration/test_order_views.py::TestOrderSubmitView -v`
Expected: FAIL — `submit_order() missing 1 required positional argument: 'actor'` (View reicht noch keinen actor durch).

- [ ] **Step 3: Write minimal implementation**

In `cmp/apps/orders/views.py`, `OrderSubmitView.post`:

```python
    def post(self, request, pk):
        try:
            OrderService.submit_order(order_id=pk, actor=request.user)
            messages.success(request, "Bestellung eingereicht.")
        except (ValidationError, ConflictError) as e:
            messages.error(request, e.message)
        return redirect("orders:detail", pk=pk)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `venv/bin/python3 -m pytest tests/integration/test_order_views.py -v`
Expected: PASS (alle)

- [ ] **Step 5: Commit**

```bash
git add cmp/apps/orders/views.py tests/integration/test_order_views.py
git commit -m "feat: AP-13 OrderSubmitView reicht actor durch

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Service-E2E an verdrahtetes Verhalten anpassen

**Files:**
- Modify: `tests/e2e/test_order_workflow.py`

**Interfaces:**
- Consumes: neue `submit_order(order_id, actor)` / `create_approval_requests(order_id, actor)`-Signaturen; Auto-Approve-Verhalten.

- [ ] **Step 1: Rewrite the E2E to match wired behavior**

`tests/e2e/test_order_workflow.py` ersetzen — kein direktes `order.status = …` mehr, neue Signaturen, Auto-Approve statt manuellem Statuswechsel:

```python
"""End-to-end test: full order lifecycle (service level)."""
import pytest
from apps.approvals.models import ApprovalRule
from apps.provisioning.models import DispatchLog
from apps.provisioning.services import ProvisioningService
from apps.approvals.services import ApprovalService
from apps.orders.services import OrderService
from apps.subscriptions.services import SubscriptionService
from core.domain.value_objects import OrderStatus
from tests.factories import UserFactory, ServiceTemplateFactory


@pytest.mark.django_db
class TestFullOrderWorkflow:
    def test_complete_lifecycle_without_approval(self):
        user = UserFactory()
        template = ServiceTemplateFactory(parameters=[
            {"key": "cpu", "type": "integer", "required": True},
        ])
        order = OrderService.create_order(user=user, notes="E2E test")
        OrderService.add_item(order.pk, template.pk, {"cpu": 4})
        order = OrderService.submit_order(order.pk, actor=user)
        # keine Regel -> auto-genehmigt
        assert order.status == OrderStatus.APPROVED

        ProvisioningService.dispatch_order(order.pk)
        order.refresh_from_db()
        assert order.status == OrderStatus.PROVISIONING

        log = DispatchLog.objects.get(order_item__order=order)
        ProvisioningService.complete_dispatch(log.pk, success=True)
        order.refresh_from_db()
        assert order.status == OrderStatus.DONE
        # Subscription automatisch angelegt
        assert SubscriptionService.list_user_subscriptions(user.pk)

    def test_complete_lifecycle_with_approval(self):
        user = UserFactory()
        approver = UserFactory(role="approver")
        template = ServiceTemplateFactory(parameters=[
            {"key": "cpu", "type": "integer", "required": True},
        ])
        ApprovalRule.objects.create(template=template, approver_role="approver")

        order = OrderService.create_order(user=user)
        OrderService.add_item(order.pk, template.pk, {"cpu": 8})
        order = OrderService.submit_order(order.pk, actor=user)
        order.refresh_from_db()
        assert order.status == OrderStatus.PENDING_APPROVAL

        from apps.approvals.models import ApprovalRequest
        req = ApprovalRequest.objects.get(order=order)
        ApprovalService.approve(req.pk, approver)
        order.refresh_from_db()
        assert order.status == OrderStatus.APPROVED

        ProvisioningService.dispatch_order(order.pk)
        log = DispatchLog.objects.get(order_item__order=order)
        ProvisioningService.complete_dispatch(log.pk, success=True)
        order.refresh_from_db()
        assert order.status == OrderStatus.DONE

    def test_rejected_order_workflow(self):
        user = UserFactory()
        approver = UserFactory(role="approver")
        template = ServiceTemplateFactory(parameters=[
            {"key": "cpu", "type": "integer", "required": True},
        ])
        ApprovalRule.objects.create(template=template, approver_role="approver")

        order = OrderService.create_order(user=user)
        OrderService.add_item(order.pk, template.pk, {"cpu": 2})
        OrderService.submit_order(order.pk, actor=user)
        from apps.approvals.models import ApprovalRequest
        req = ApprovalRequest.objects.get(order=order)
        ApprovalService.reject(req.pk, approver, comment="Budget exceeded")
        order.refresh_from_db()
        assert order.status == OrderStatus.REJECTED

    def test_failed_provisioning_workflow(self):
        user = UserFactory()
        template = ServiceTemplateFactory(parameters=[
            {"key": "cpu", "type": "integer", "required": True},
        ])
        order = OrderService.create_order(user=user)
        OrderService.add_item(order.pk, template.pk, {"cpu": 4})
        order = OrderService.submit_order(order.pk, actor=user)
        assert order.status == OrderStatus.APPROVED

        ProvisioningService.dispatch_order(order.pk)
        log = DispatchLog.objects.get(order_item__order=order)
        ProvisioningService.complete_dispatch(log.pk, success=False)
        order.refresh_from_db()
        assert order.status == OrderStatus.FAILED
```

- [ ] **Step 2: Run test to verify it passes**

Run: `venv/bin/python3 -m pytest tests/e2e/test_order_workflow.py -v`
Expected: PASS (4 passed)

- [ ] **Step 3: Commit**

```bash
git add tests/e2e/test_order_workflow.py
git commit -m "test: AP-13 Service-E2E an verdrahtete Kette angepasst

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: Wächter-Test — keine direkte `order.status`-Zuweisung außerhalb `transitions.py`

**Files:**
- Create: `tests/unit/test_no_direct_status.py`

**Interfaces:**
- Consumes: den Quellbaum `cmp/apps` + `cmp/core` (AST-Scan).
- Produces: `test_no_direct_order_status_assignment_outside_transitions` — schlägt fehl, sobald irgendwo außer `apps/orders/transitions.py` ein `<order-artig>.status = …` steht.

- [ ] **Step 1: Write the test (soll direkt grün sein, weil Tasks 3–5 alles migriert haben)**

```python
# tests/unit/test_no_direct_status.py
"""Waechter: order.status darf nur in apps/orders/transitions.py gesetzt werden."""
import ast
from pathlib import Path

CMP_ROOT = Path(__file__).resolve().parents[2] / "cmp"
ALLOWED = {CMP_ROOT / "apps" / "orders" / "transitions.py"}


def _order_status_assignments(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AugAssign):
            targets = [node.target]
        else:
            continue
        for target in targets:
            if not (isinstance(target, ast.Attribute) and target.attr == "status"):
                continue
            base = target.value
            name = base.id if isinstance(base, ast.Name) else (
                base.attr if isinstance(base, ast.Attribute) else "")
            if "order" in name.lower():   # order.status, req.order.status, ...
                hits.append(node.lineno)
    return hits


def test_no_direct_order_status_assignment_outside_transitions():
    offenders = []
    files = list((CMP_ROOT / "apps").rglob("*.py")) + list(
        (CMP_ROOT / "core").rglob("*.py"))
    for path in files:
        if path in ALLOWED or "migrations" in path.parts:
            continue
        for lineno in _order_status_assignments(path):
            offenders.append(f"{path.relative_to(CMP_ROOT)}:{lineno}")
    assert not offenders, (
        "Direkte order.status-Zuweisung ausserhalb transitions.py:\n"
        + "\n".join(offenders)
    )
```

- [ ] **Step 2: Run it — expect PASS**

Run: `venv/bin/python3 -m pytest tests/unit/test_no_direct_status.py -v`
Expected: PASS (alle `order.status`-Zuweisungen laufen jetzt über `transition()`).

Falls FAIL: die gemeldeten Stellen (`datei:zeile`) noch auf `transition()` umstellen, dann erneut laufen lassen.

- [ ] **Step 3: Fehlerinjektion — beweisen, dass der Test beißt**

Vorübergehend in `cmp/apps/approvals/services.py` in `reject()` VOR dem `transition(...)` eine Zeile einfügen: `req.order.status = OrderStatus.REJECTED` — dann:

Run: `venv/bin/python3 -m pytest tests/unit/test_no_direct_status.py -v`
Expected: FAIL — nennt `apps/approvals/services.py:<zeile>`.

Danach die eingefügte Zeile wieder entfernen und erneut laufen lassen → PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/unit/test_no_direct_status.py
git commit -m "test: AP-13 Waechter gegen direkte order.status-Zuweisung (AST)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 9: DoD-E2E — die Kette durch die Views

**Files:**
- Create: `tests/e2e/test_workflow_through_views.py`

**Interfaces:**
- Consumes: URLs `orders:submit`, `approvals:approve`; `django_capture_on_commit_callbacks`-Fixture (pytest-django); Modelle für die Assertions.
- Produces: der DoD-Nachweis — `POST orders:submit` → Queue enthält Request → `POST approvals:approve` → Order `DONE`, Subscription existiert, Audit-Log gefüllt, Besteller benachrichtigt; **kein direkter Service-Aufruf im Testkörper**.

- [ ] **Step 1: Write the failing test**

```python
# tests/e2e/test_workflow_through_views.py
"""DoD-E2E: die komplette Bestellkette ausgeloest durch die Views."""
import pytest
from django.urls import reverse

from apps.approvals.models import ApprovalRule, ApprovalRequest
from apps.audit.models import AuditLog
from apps.notifications.models import Notification
from apps.subscriptions.models import Subscription
from core.domain.value_objects import OrderStatus
from tests.factories import (
    UserFactory, ServiceTemplateFactory, OrderFactory, OrderItemFactory,
)


@pytest.mark.django_db
class TestWorkflowThroughViews:
    def test_submit_approve_provision_done(self, client, django_capture_on_commit_callbacks):
        requester = UserFactory(role="requester")
        approver = UserFactory(role="approver")
        template = ServiceTemplateFactory(parameters=[
            {"key": "cpu", "type": "integer", "required": True},
        ])
        ApprovalRule.objects.create(template=template, approver_role="approver")
        order = OrderFactory(user=requester)
        OrderItemFactory(order=order, template=template, parameters={"cpu": 4})

        # --- einreichen durch den View ---
        client.force_login(requester)
        with django_capture_on_commit_callbacks(execute=True):
            r1 = client.post(reverse("orders:submit", kwargs={"pk": order.pk}))
        assert r1.status_code == 302
        order.refresh_from_db()
        assert order.status == OrderStatus.PENDING_APPROVAL
        req = ApprovalRequest.objects.get(order=order)
        assert req.status == "pending"
        assert Notification.objects.filter(
            user=approver, title="Neue Genehmigung erforderlich"
        ).exists()

        # --- genehmigen durch den View: on_commit feuert die ganze Kette ---
        client.force_login(approver)
        with django_capture_on_commit_callbacks(execute=True):
            r2 = client.post(reverse("approvals:approve", kwargs={"pk": req.pk}))
        assert r2.status_code == 302
        order.refresh_from_db()
        assert order.status == OrderStatus.DONE
        assert Subscription.objects.filter(user=requester).exists()
        assert AuditLog.objects.filter(
            resource_type="order", resource_id=order.pk, action="order.done"
        ).exists()
        assert Notification.objects.filter(
            user=requester, title="Bestellung abgeschlossen"
        ).exists()
```

- [ ] **Step 2: Run test to verify it fails first, then passes**

Run: `venv/bin/python3 -m pytest tests/e2e/test_workflow_through_views.py -v`
Expected: PASS, sofern Tasks 1–5 vollständig sind. Falls FAIL bei `order.status == DONE`: prüfen, dass `approve()` `transaction.on_commit(dispatch_provisioning.delay)` registriert und der `dispatch_provisioning`-Task die laufenden Logs sofort abschließt (Task 5).

- [ ] **Step 3: Commit**

```bash
git add tests/e2e/test_workflow_through_views.py
git commit -m "test: AP-13 DoD-E2E durch die Views (submit -> approve -> DONE)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 10: Gesamt-Suite grün + Doku-Nachzug

**Files:**
- Modify: `todo.md`, ggf. `CHANGELOG.md` / Doku (nur falls im Release-Schritt gefordert)

- [ ] **Step 1: Volle Testsuite laufen lassen**

Run: `venv/bin/python3 -m pytest -q`
Expected: alle Tests grün (347 vorher + neue). Rote Tests sind fast immer übersehene Signatur-/Verhaltensanpassungen aus Tasks 3–7 → dort nachziehen.

- [ ] **Step 2: `seed.py` gegen die neuen Signaturen prüfen**

Run: `grep -rn "submit_order\|create_approval_requests" cmp/ --include=*.py | grep -v tests`
Erwartung: außer den Service-/View-Definitionen keine Aufrufer mit alter Signatur. Falls `seed.py` `submit_order`/`create_approval_requests` aufruft, `actor` ergänzen.

- [ ] **Step 3: AP-13 in `todo.md` abhaken**

Die sechs Lücken-Checkboxen + Wächter-Test + DoD unter `## AP-13` auf `[x]` setzen.

- [ ] **Step 4: Commit**

```bash
git add todo.md
git commit -m "docs: AP-13 als erledigt markiert (Bestellkette verdrahtet)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

Hinweis: Der vollständige Doku-/Release-Nachzug (Changelog EN+DE, Roadmap/Gantt, Kennzahlen, Handoff/KPI) folgt separat über den Session-Handoff-Prozess und das Doku-Gate (`cmp-docs/verify_docs.sh`) — nicht Teil dieses Implementierungsplans.

---

## Self-Review

**Spec-Abdeckung (die 6 Lücken + Rahmen):**
- Lücke 1 (submit → create_approval_requests / Auto-Approve): Task 4 ✓
- Lücke 2 (approve → on_commit dispatch): Task 3 ✓
- Lücke 3 (Rückmeldung → complete_dispatch, Stub sofort): Task 5 ✓
- Lücke 4 (DONE → create_from_order): Task 5 ✓
- Lücke 5 (approve/reject/submit/provisioning auf transition()): Tasks 3,4,5 ✓
- Lücke 6 (Benachrichtigungen Genehmiger/Besteller): Tasks 3,4,5 ✓
- `transition()` in apps/orders (nicht core): Task 1 ✓
- Wächter-Test (AST) + Fehlerinjektion: Task 8 ✓
- E2E durch die Views + on_commit-Falle: Task 9 ✓
- Actor-Threading (Signaturen submit_order/create_approval_requests): Tasks 3,4,6 ✓
- Genehmiger-Empfänger-Helfer: Task 2 ✓
- Bruch bestehender Tests aufgefangen: Tasks 3,4,5,6,7 + Task 10 (Suite) ✓

**Placeholder-Scan:** keine TBD/TODO/„handle edge cases" — alle Steps enthalten echten Code.

**Typ-/Signatur-Konsistenz:** `transition(order, to_status, actor, **details)` einheitlich in allen Tasks; `submit_order(order_id, actor)` und `create_approval_requests(order_id, actor)` durchgängig (Def in 3/4, Aufrufer in 4/6/7/9); `list_users_with_min_role(minimum_role)` Def Task 2, Nutzung Task 4.

**Bewusst außerhalb Scope (YAGNI):** AP-14 Logging, AP-18 E-Mail, AP-20 echter GitLab-Client + Polling.
