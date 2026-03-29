# Phase B5: Provisioning Engine — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement async provisioning via Celery tasks — GitLab stub client triggers simulated pipelines, DispatchLog tracks status, order status transitions from approved → provisioning → done/failed.

**Architecture:** `apps/provisioning/` with models (DispatchLog), services (ProvisioningService), tasks (Celery), clients (GitLabStubClient). Celery configured with Redis broker, ALWAYS_EAGER in testing.

**Tech Stack:** Django 6.0, Celery, Redis, pytest-django

---

## File Structure

```
mpp/config/
└── celery.py                # Celery app

mpp/apps/provisioning/
├── __init__.py
├── apps.py
├── models.py                # DispatchLog
├── services.py              # ProvisioningService
├── tasks.py                 # Celery tasks
├── clients.py               # GitLabStubClient / GitLabLiveClient
├── admin.py
└── urls.py

tests/
├── unit/
│   ├── test_provisioning_client.py
│   └── test_provisioning_service.py
└── integration/
    └── test_dispatch_model.py
```

---

## Task 1: Celery Configuration

**Files:**
- Create: `mpp/config/celery.py`
- Modify: `mpp/config/__init__.py`
- Modify: `mpp/config/settings/base.py` (Celery settings)
- Modify: `mpp/config/settings/testing.py` (ALWAYS_EAGER)
- Modify: `requirements/base.txt` (add celery, redis)

- [ ] **Step 1: Add dependencies**

Add to `requirements/base.txt`:
```
celery>=5.4,<6.0
redis>=5.0,<6.0
```

Run: `pip install celery redis`

- [ ] **Step 2: Create config/celery.py**

```python
"""Celery application configuration."""
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("mpp")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

- [ ] **Step 3: Update config/__init__.py**

```python
from .celery import app as celery_app

__all__ = ("celery_app",)
```

- [ ] **Step 4: Add Celery settings**

In `mpp/config/settings/base.py`:
```python
# Celery
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
CELERY_TASK_ALWAYS_EAGER = False
```

In `mpp/config/settings/testing.py`:
```python
# Celery — run tasks synchronously in tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
```

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(B5): add Celery configuration with Redis broker"
```

---

## Task 2: GitLab Stub Client

**Files:**
- Create: `mpp/apps/provisioning/__init__.py`, `apps.py`, `clients.py`
- Test: `tests/unit/test_provisioning_client.py`

- [ ] **Step 1: Write failing tests**

```python
"""Test GitLab stub client."""
from apps.provisioning.clients import GitLabStubClient

class TestGitLabStubClient:
    def setup_method(self):
        self.client = GitLabStubClient()

    def test_trigger_pipeline_returns_pipeline_id(self):
        result = self.client.trigger_pipeline("Linux VM", {"cpu": 4})
        assert "pipeline_id" in result
        assert isinstance(result["pipeline_id"], str)
        assert len(result["pipeline_id"]) > 0

    def test_trigger_pipeline_returns_status_running(self):
        result = self.client.trigger_pipeline("Linux VM", {"cpu": 4})
        assert result["status"] == "running"

    def test_pipeline_ids_are_unique(self):
        r1 = self.client.trigger_pipeline("VM", {})
        r2 = self.client.trigger_pipeline("VM", {})
        assert r1["pipeline_id"] != r2["pipeline_id"]

    def test_get_pipeline_status_returns_none_for_unknown(self):
        status = self.client.get_pipeline_status("nonexistent")
        assert status is None

    def test_complete_pipeline(self):
        result = self.client.trigger_pipeline("VM", {})
        pid = result["pipeline_id"]
        self.client.complete_pipeline(pid, success=True)
        status = self.client.get_pipeline_status(pid)
        assert status == "success"

    def test_fail_pipeline(self):
        result = self.client.trigger_pipeline("VM", {})
        pid = result["pipeline_id"]
        self.client.complete_pipeline(pid, success=False)
        status = self.client.get_pipeline_status(pid)
        assert status == "failed"
```

- [ ] **Step 2: Implement**

```python
"""GitLab pipeline clients."""
import uuid

class GitLabStubClient:
    """Simulates GitLab pipeline triggers in memory."""
    def __init__(self):
        self._pipelines = {}

    def trigger_pipeline(self, template_name, parameters):
        pipeline_id = uuid.uuid4().hex[:12]
        self._pipelines[pipeline_id] = "running"
        return {"pipeline_id": pipeline_id, "status": "running"}

    def get_pipeline_status(self, pipeline_id):
        return self._pipelines.get(pipeline_id)

    def complete_pipeline(self, pipeline_id, success=True):
        if pipeline_id in self._pipelines:
            self._pipelines[pipeline_id] = "success" if success else "failed"
```

Commit: `git commit -m "feat(B5): add GitLab stub client for pipeline simulation"`

---

## Task 3: DispatchLog Model

**Files:**
- Create: `mpp/apps/provisioning/models.py`, `admin.py`
- Modify: `mpp/config/settings/base.py` (add apps.provisioning)
- Test: `tests/integration/test_dispatch_model.py`

- [ ] **Step 1: Write failing tests**

```python
"""Test DispatchLog model."""
import pytest
from apps.provisioning.models import DispatchLog
from tests.factories import OrderItemFactory

@pytest.mark.django_db
class TestDispatchLogModel:
    def test_create_dispatch_log(self):
        item = OrderItemFactory()
        log = DispatchLog.objects.create(
            order_item=item, pipeline_id="abc123", status="running",
            payload={"template": "Linux VM", "params": {"cpu": 4}},
        )
        assert log.pk is not None
        assert log.status == "running"

    def test_str(self):
        item = OrderItemFactory()
        log = DispatchLog.objects.create(order_item=item, pipeline_id="abc123", status="running")
        assert "abc123" in str(log)

    def test_has_timestamps(self):
        item = OrderItemFactory()
        log = DispatchLog.objects.create(order_item=item, pipeline_id="abc123", status="running")
        assert log.dispatched_at is not None

    def test_completed_at_nullable(self):
        item = OrderItemFactory()
        log = DispatchLog.objects.create(order_item=item, pipeline_id="abc123", status="running")
        assert log.completed_at is None

    def test_default_payload_is_empty_dict(self):
        item = OrderItemFactory()
        log = DispatchLog.objects.create(order_item=item, pipeline_id="abc123", status="running")
        assert log.payload == {}
```

- [ ] **Step 2: Implement**

```python
from django.db import models
from core.mixins import TimeStampedModel

class DispatchLog(TimeStampedModel):
    order_item = models.ForeignKey("orders.OrderItem", on_delete=models.CASCADE, related_name="dispatch_logs")
    pipeline_id = models.CharField(max_length=100)
    status = models.CharField(max_length=30, default="pending")
    payload = models.JSONField(default=dict)
    dispatched_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "dispatch_logs"
        ordering = ["-dispatched_at"]

    def __str__(self):
        return f"Dispatch {self.pipeline_id} ({self.status})"
```

Commit: `git commit -m "feat(B5): add DispatchLog model"`

---

## Task 4: ProvisioningService + Celery Tasks

**Files:**
- Create: `mpp/apps/provisioning/services.py`
- Create: `mpp/apps/provisioning/tasks.py`
- Test: `tests/unit/test_provisioning_service.py`

- [ ] **Step 1: Write failing tests**

```python
"""Test ProvisioningService."""
import pytest
from apps.orders.models import Order
from apps.provisioning.models import DispatchLog
from apps.provisioning.services import ProvisioningService
from core.domain.value_objects import OrderStatus
from core.exceptions import ConflictError, NotFoundError
from tests.factories import OrderFactory, OrderItemFactory

@pytest.mark.django_db
class TestProvisioningServiceDispatch:
    def test_dispatch_order(self):
        order = OrderFactory(status=OrderStatus.APPROVED)
        item = OrderItemFactory(order=order)
        ProvisioningService.dispatch_order(order.pk)
        order.refresh_from_db()
        assert order.status == OrderStatus.PROVISIONING
        assert DispatchLog.objects.filter(order_item=item).count() == 1

    def test_dispatch_creates_log_per_item(self):
        order = OrderFactory(status=OrderStatus.APPROVED)
        OrderItemFactory(order=order)
        OrderItemFactory(order=order)
        ProvisioningService.dispatch_order(order.pk)
        assert DispatchLog.objects.count() == 2

    def test_dispatch_non_approved_raises(self):
        order = OrderFactory(status=OrderStatus.DRAFT)
        with pytest.raises(ConflictError):
            ProvisioningService.dispatch_order(order.pk)

    def test_dispatch_nonexistent_raises(self):
        with pytest.raises(NotFoundError):
            ProvisioningService.dispatch_order(99999)

@pytest.mark.django_db
class TestProvisioningServiceComplete:
    def test_complete_item_success(self):
        order = OrderFactory(status=OrderStatus.PROVISIONING)
        item = OrderItemFactory(order=order)
        log = DispatchLog.objects.create(order_item=item, pipeline_id="abc", status="running")
        ProvisioningService.complete_dispatch(log.pk, success=True)
        log.refresh_from_db()
        assert log.status == "success"
        assert log.completed_at is not None

    def test_complete_item_failure(self):
        order = OrderFactory(status=OrderStatus.PROVISIONING)
        item = OrderItemFactory(order=order)
        log = DispatchLog.objects.create(order_item=item, pipeline_id="abc", status="running")
        ProvisioningService.complete_dispatch(log.pk, success=False)
        log.refresh_from_db()
        assert log.status == "failed"

    def test_all_items_done_completes_order(self):
        order = OrderFactory(status=OrderStatus.PROVISIONING)
        item = OrderItemFactory(order=order)
        log = DispatchLog.objects.create(order_item=item, pipeline_id="abc", status="running")
        ProvisioningService.complete_dispatch(log.pk, success=True)
        order.refresh_from_db()
        assert order.status == OrderStatus.DONE

    def test_any_item_failed_fails_order(self):
        order = OrderFactory(status=OrderStatus.PROVISIONING)
        item1 = OrderItemFactory(order=order)
        item2 = OrderItemFactory(order=order)
        log1 = DispatchLog.objects.create(order_item=item1, pipeline_id="a", status="running")
        log2 = DispatchLog.objects.create(order_item=item2, pipeline_id="b", status="running")
        ProvisioningService.complete_dispatch(log1.pk, success=True)
        ProvisioningService.complete_dispatch(log2.pk, success=False)
        order.refresh_from_db()
        assert order.status == OrderStatus.FAILED
```

- [ ] **Step 2: Implement ProvisioningService**

```python
from django.utils import timezone
from apps.orders.services import OrderService
from apps.provisioning.clients import GitLabStubClient
from apps.provisioning.models import DispatchLog
from core.domain.value_objects import OrderStatus, StatusMachine
from core.exceptions import ConflictError, NotFoundError

class ProvisioningService:
    @staticmethod
    def dispatch_order(order_id):
        order = OrderService.get_order(order_id)
        if order.status != OrderStatus.APPROVED:
            raise ConflictError(f"Cannot dispatch order in status '{order.status}'.")

        StatusMachine.validate_transition(order.status, OrderStatus.PROVISIONING)
        order.status = OrderStatus.PROVISIONING
        order.save()

        client = GitLabStubClient()
        for item in order.items.select_related("template").all():
            result = client.trigger_pipeline(item.template.name, item.parameters)
            DispatchLog.objects.create(
                order_item=item,
                pipeline_id=result["pipeline_id"],
                status="running",
                payload={"template": item.template.name, "parameters": item.parameters},
            )

    @staticmethod
    def complete_dispatch(dispatch_log_id, success=True):
        try:
            log = DispatchLog.objects.select_related("order_item__order").get(pk=dispatch_log_id)
        except DispatchLog.DoesNotExist:
            raise NotFoundError(f"DispatchLog with id={dispatch_log_id} not found.")

        log.status = "success" if success else "failed"
        log.completed_at = timezone.now()
        log.save()

        order = log.order_item.order
        all_logs = DispatchLog.objects.filter(order_item__order=order)

        if all_logs.filter(status="running").exists():
            return  # Still pending

        if all_logs.filter(status="failed").exists():
            order.status = OrderStatus.FAILED
        else:
            order.status = OrderStatus.DONE
        order.save()
```

- [ ] **Step 3: Create tasks.py** (simple wrapper for async dispatch)

```python
from celery import shared_task
from .services import ProvisioningService

@shared_task
def dispatch_provisioning(order_id):
    ProvisioningService.dispatch_order(order_id)

@shared_task
def complete_provisioning(dispatch_log_id, success=True):
    ProvisioningService.complete_dispatch(dispatch_log_id, success=success)
```

Run ALL: `python -m pytest tests/ -v`
Commit: `git commit -m "feat(B5): add ProvisioningService with dispatch, complete, and Celery tasks"`

---

## Summary

| Task | Description | Tests |
|------|-------------|-------|
| 1 | Celery config | 0 |
| 2 | GitLab stub client | 6 |
| 3 | DispatchLog model | 5 |
| 4 | ProvisioningService + tasks | 8 |
| **Total new** | | **~19** |
| **Running total** | | **~181** |
