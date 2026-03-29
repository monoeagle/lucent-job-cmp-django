# Phase B8: Subscriptions — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement subscription management — active services from completed orders, with change and cancel workflows.

**Architecture:** `apps/subscriptions/` with Subscription + GroupSubscription models, SubscriptionService, views.

**Tech Stack:** Django 6.0, pytest-django, factory_boy

---

## Task 1: Subscription Models

Add `"apps.subscriptions"` to INSTALLED_APPS.

**Test** `tests/integration/test_subscription_model.py`:
```python
import pytest
from django.utils import timezone
from apps.subscriptions.models import Subscription, GroupSubscription
from tests.factories import UserFactory, OrderItemFactory, OrderFactory, ServiceTemplateFactory

@pytest.mark.django_db
class TestSubscriptionModel:
    def test_create(self):
        user = UserFactory()
        item = OrderItemFactory()
        s = Subscription.objects.create(user=user, order_item=item, status="active")
        assert s.pk is not None

    def test_str(self):
        user = UserFactory(username="testuser")
        item = OrderItemFactory()
        s = Subscription.objects.create(user=user, order_item=item, status="active")
        assert "testuser" in str(s)

    def test_valid_from_default(self):
        user = UserFactory()
        item = OrderItemFactory()
        s = Subscription.objects.create(user=user, order_item=item, status="active")
        assert s.valid_from is not None

    def test_valid_until_nullable(self):
        user = UserFactory()
        item = OrderItemFactory()
        s = Subscription.objects.create(user=user, order_item=item, status="active")
        assert s.valid_until is None

@pytest.mark.django_db
class TestGroupSubscriptionModel:
    def test_create(self):
        from apps.orders.models import OrderItemGroup, Order
        user = UserFactory()
        template = ServiceTemplateFactory()
        order = Order.objects.create(user=user)
        group = OrderItemGroup.objects.create(order=order, template=template, quantity=3)
        gs = GroupSubscription.objects.create(user=user, order_item_group=group, status="active")
        assert gs.pk is not None
```

**Models** `mpp/apps/subscriptions/models.py`:
```python
from django.conf import settings
from django.db import models
from core.mixins import TimeStampedModel

class Subscription(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions")
    order_item = models.ForeignKey("orders.OrderItem", on_delete=models.CASCADE, related_name="subscriptions")
    status = models.CharField(max_length=30, default="active")
    valid_from = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    class Meta:
        db_table = "subscriptions"
        ordering = ["-created_at"]
    def __str__(self):
        return f"Sub: {self.user.username} - {self.order_item.template.name} ({self.status})"

class GroupSubscription(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="group_subscriptions")
    order_item_group = models.ForeignKey("orders.OrderItemGroup", on_delete=models.CASCADE, related_name="subscriptions")
    status = models.CharField(max_length=30, default="active")
    class Meta:
        db_table = "group_subscriptions"
    def __str__(self):
        return f"GroupSub: {self.user.username} ({self.status})"
```

Commit: `git commit -m "feat(B8): add Subscription and GroupSubscription models"`

---

## Task 2: SubscriptionService

**Test** `tests/unit/test_subscription_service.py`:
```python
import pytest
from apps.subscriptions.models import Subscription
from apps.subscriptions.services import SubscriptionService
from core.domain.value_objects import OrderStatus
from core.exceptions import ConflictError, NotFoundError
from tests.factories import UserFactory, OrderFactory, OrderItemFactory

@pytest.mark.django_db
class TestSubscriptionServiceCreate:
    def test_create_from_completed_order(self):
        user = UserFactory()
        order = OrderFactory(user=user, status=OrderStatus.DONE)
        item = OrderItemFactory(order=order)
        subs = SubscriptionService.create_from_order(order.pk)
        assert len(subs) == 1
        assert subs[0].user == user
        assert subs[0].status == "active"

    def test_create_from_non_done_raises(self):
        order = OrderFactory(status=OrderStatus.DRAFT)
        with pytest.raises(ConflictError):
            SubscriptionService.create_from_order(order.pk)

@pytest.mark.django_db
class TestSubscriptionServiceList:
    def test_list_user_subscriptions(self):
        user = UserFactory()
        order = OrderFactory(user=user, status=OrderStatus.DONE)
        item = OrderItemFactory(order=order)
        SubscriptionService.create_from_order(order.pk)
        subs = SubscriptionService.list_user_subscriptions(user.pk)
        assert len(subs) == 1

    def test_empty_when_no_subs(self):
        user = UserFactory()
        assert len(SubscriptionService.list_user_subscriptions(user.pk)) == 0

@pytest.mark.django_db
class TestSubscriptionServiceCancel:
    def test_cancel(self):
        user = UserFactory()
        order = OrderFactory(user=user, status=OrderStatus.DONE)
        item = OrderItemFactory(order=order)
        subs = SubscriptionService.create_from_order(order.pk)
        SubscriptionService.cancel(subs[0].pk)
        subs[0].refresh_from_db()
        assert subs[0].status == "cancelled"

    def test_cancel_already_cancelled_raises(self):
        user = UserFactory()
        order = OrderFactory(user=user, status=OrderStatus.DONE)
        item = OrderItemFactory(order=order)
        subs = SubscriptionService.create_from_order(order.pk)
        SubscriptionService.cancel(subs[0].pk)
        with pytest.raises(ConflictError):
            SubscriptionService.cancel(subs[0].pk)
```

**Service** `mpp/apps/subscriptions/services.py`:
```python
from django.utils import timezone
from apps.orders.services import OrderService
from apps.subscriptions.models import Subscription
from core.domain.value_objects import OrderStatus
from core.exceptions import ConflictError, NotFoundError

class SubscriptionService:
    @staticmethod
    def create_from_order(order_id):
        order = OrderService.get_order(order_id)
        if order.status != OrderStatus.DONE:
            raise ConflictError("Subscriptions can only be created from completed orders.")
        subs = []
        for item in order.items.all():
            sub = Subscription.objects.create(user=order.user, order_item=item, status="active")
            subs.append(sub)
        return subs

    @staticmethod
    def list_user_subscriptions(user_id):
        return list(Subscription.objects.filter(user_id=user_id).select_related("order_item__template"))

    @staticmethod
    def get_subscription(sub_id):
        try:
            return Subscription.objects.get(pk=sub_id)
        except Subscription.DoesNotExist:
            raise NotFoundError(f"Subscription {sub_id} not found.")

    @staticmethod
    def cancel(sub_id):
        sub = SubscriptionService.get_subscription(sub_id)
        if sub.status != "active":
            raise ConflictError(f"Cannot cancel subscription in status '{sub.status}'.")
        sub.status = "cancelled"
        sub.valid_until = timezone.now()
        sub.save()
```

Commit: `git commit -m "feat(B8): add SubscriptionService with create, list, cancel"`

---

## Task 3: Subscription Views & Templates

**Test** `tests/integration/test_subscription_views.py`:
```python
import pytest
from django.urls import reverse
from apps.subscriptions.models import Subscription
from core.domain.value_objects import OrderStatus
from tests.factories import UserFactory, OrderFactory, OrderItemFactory

@pytest.mark.django_db
class TestSubscriptionViews:
    def test_list_requires_login(self, client):
        assert client.get(reverse("subscriptions:list")).status_code == 302

    def test_list_returns_200(self, client):
        user = UserFactory()
        client.force_login(user)
        assert client.get(reverse("subscriptions:list")).status_code == 200

    def test_detail_returns_200(self, client):
        user = UserFactory()
        order = OrderFactory(user=user, status=OrderStatus.DONE)
        item = OrderItemFactory(order=order)
        sub = Subscription.objects.create(user=user, order_item=item, status="active")
        client.force_login(user)
        assert client.get(reverse("subscriptions:detail", kwargs={"pk": sub.pk})).status_code == 200

    def test_cancel(self, client):
        user = UserFactory()
        order = OrderFactory(user=user, status=OrderStatus.DONE)
        item = OrderItemFactory(order=order)
        sub = Subscription.objects.create(user=user, order_item=item, status="active")
        client.force_login(user)
        response = client.post(reverse("subscriptions:cancel", kwargs={"pk": sub.pk}))
        assert response.status_code == 302
        sub.refresh_from_db()
        assert sub.status == "cancelled"
```

**Views** + **URLs** + **Templates** (list, detail, cancel action).

Add `path("subscriptions/", include("apps.subscriptions.urls"))` to config/urls.py.

Commit: `git commit -m "feat(B8): add subscription views with list, detail, cancel"`

Run ALL: `python -m pytest tests/ -v` — expect ~236 passed.

---

## Summary

| Task | Description | Tests |
|------|-------------|-------|
| 1 | Subscription + GroupSubscription models | 5 |
| 2 | SubscriptionService | 6 |
| 3 | Subscription views + templates | 4 |
| **Total new** | | **~15** |
| **Running total** | | **~234** |
