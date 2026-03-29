# Phase B7: Cross-Cutting Concerns — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement audit logging, in-app notifications, and an admin dashboard with statistics.

**Architecture:** `apps/audit/` (AuditLog model + service), `apps/notifications/` (Notification model + service), dashboard stats view.

**Tech Stack:** Django 6.0, pytest-django, factory_boy

---

## Task 1: AuditLog Model & Service

**Models:** AuditLog with user, action, resource_type, resource_id, details (JSON), ip_address, timestamp.

**Tests** `tests/unit/test_audit_service.py`:
```python
import pytest
from apps.audit.models import AuditLog
from apps.audit.services import AuditService
from tests.factories import UserFactory

@pytest.mark.django_db
class TestAuditService:
    def test_log_action(self):
        user = UserFactory()
        AuditService.log(user=user, action="order_created", resource_type="order", resource_id=1)
        assert AuditLog.objects.count() == 1

    def test_log_with_details(self):
        user = UserFactory()
        AuditService.log(user=user, action="order_submitted", resource_type="order", resource_id=1, details={"items": 3})
        log = AuditLog.objects.first()
        assert log.details == {"items": 3}

    def test_log_without_user(self):
        AuditService.log(user=None, action="system_startup", resource_type="system", resource_id=0)
        assert AuditLog.objects.count() == 1

    def test_list_logs(self):
        user = UserFactory()
        AuditService.log(user=user, action="a1", resource_type="order", resource_id=1)
        AuditService.log(user=user, action="a2", resource_type="order", resource_id=2)
        logs = AuditService.list_logs()
        assert len(logs) == 2

    def test_list_logs_by_resource_type(self):
        user = UserFactory()
        AuditService.log(user=user, action="a1", resource_type="order", resource_id=1)
        AuditService.log(user=user, action="a2", resource_type="template", resource_id=1)
        logs = AuditService.list_logs(resource_type="order")
        assert len(logs) == 1

    def test_anonymize_user(self):
        user = UserFactory()
        AuditService.log(user=user, action="a1", resource_type="order", resource_id=1)
        AuditService.anonymize_user(user.pk)
        log = AuditLog.objects.first()
        assert log.user is None
```

---

## Task 2: Notification Model & Service

**Tests** `tests/unit/test_notification_service.py`:
```python
import pytest
from apps.notifications.models import Notification
from apps.notifications.services import NotificationService
from tests.factories import UserFactory

@pytest.mark.django_db
class TestNotificationService:
    def test_create_notification(self):
        user = UserFactory()
        n = NotificationService.create(user=user, title="Test", message="Hello")
        assert n.pk is not None
        assert n.is_read is False

    def test_list_unread(self):
        user = UserFactory()
        NotificationService.create(user=user, title="Unread", message="msg")
        NotificationService.create(user=user, title="Read", message="msg")
        Notification.objects.filter(title="Read").update(is_read=True)
        unread = NotificationService.list_unread(user.pk)
        assert len(unread) == 1

    def test_mark_read(self):
        user = UserFactory()
        n = NotificationService.create(user=user, title="Test", message="msg")
        NotificationService.mark_read(n.pk)
        n.refresh_from_db()
        assert n.is_read is True

    def test_mark_all_read(self):
        user = UserFactory()
        NotificationService.create(user=user, title="A", message="msg")
        NotificationService.create(user=user, title="B", message="msg")
        NotificationService.mark_all_read(user.pk)
        assert Notification.objects.filter(user=user, is_read=False).count() == 0

    def test_unread_count(self):
        user = UserFactory()
        NotificationService.create(user=user, title="A", message="msg")
        NotificationService.create(user=user, title="B", message="msg")
        assert NotificationService.unread_count(user.pk) == 2

    def test_list_all(self):
        user = UserFactory()
        NotificationService.create(user=user, title="A", message="msg")
        all_notifs = NotificationService.list_all(user.pk)
        assert len(all_notifs) == 1
```

---

## Task 3: Notification & Audit Views

Notification views: list, mark-read (HTMX), mark-all-read.
Audit view: admin-only log list with filters.

**Tests** `tests/integration/test_notification_views.py`:
```python
import pytest
from django.urls import reverse
from apps.notifications.services import NotificationService
from core.domain.enums import UserRole
from tests.factories import UserFactory

@pytest.mark.django_db
class TestNotificationViews:
    def test_list_requires_login(self, client):
        response = client.get(reverse("notifications:list"))
        assert response.status_code == 302

    def test_list_returns_200(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("notifications:list"))
        assert response.status_code == 200

    def test_mark_read(self, client):
        user = UserFactory()
        n = NotificationService.create(user=user, title="Test", message="msg")
        client.force_login(user)
        response = client.post(reverse("notifications:mark_read", kwargs={"pk": n.pk}))
        assert response.status_code == 302
        n.refresh_from_db()
        assert n.is_read is True

    def test_mark_all_read(self, client):
        user = UserFactory()
        NotificationService.create(user=user, title="A", message="msg")
        client.force_login(user)
        response = client.post(reverse("notifications:mark_all_read"))
        assert response.status_code == 302
```

**Tests** `tests/integration/test_audit_views.py`:
```python
import pytest
from django.urls import reverse
from apps.audit.services import AuditService
from core.domain.enums import UserRole
from tests.factories import UserFactory

@pytest.mark.django_db
class TestAuditViews:
    def test_requires_admin(self, client):
        user = UserFactory(role=UserRole.REQUESTER)
        client.force_login(user)
        response = client.get(reverse("audit:list"))
        assert response.status_code == 403

    def test_admin_can_access(self, client):
        user = UserFactory(role=UserRole.ADMIN)
        client.force_login(user)
        response = client.get(reverse("audit:list"))
        assert response.status_code == 200
```

---

## Task 4: Dashboard Stats

Update dashboard view to show real statistics.

**Tests** `tests/integration/test_dashboard_stats.py`:
```python
import pytest
from django.urls import reverse
from tests.factories import UserFactory, OrderFactory

@pytest.mark.django_db
class TestDashboardStats:
    def test_dashboard_shows_order_count(self, client):
        user = UserFactory()
        OrderFactory(user=user)
        OrderFactory(user=user)
        client.force_login(user)
        response = client.get(reverse("dashboard:home"))
        assert response.status_code == 200
```

---

## Summary

| Task | Description | Tests |
|------|-------------|-------|
| 1 | AuditLog model + AuditService | 6 |
| 2 | Notification model + NotificationService | 6 |
| 3 | Notification + Audit views | 6 |
| 4 | Dashboard stats | 1 |
| **Total new** | | **~19** |
| **Running total** | | **~219** |
