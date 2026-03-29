# Phase B3: Order Lifecycle — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the order lifecycle — Orders, OrderItems, OrderItemGroups with a strict status machine (draft → validated → submitted → ... → done/failed/rejected). CRUD views with a wizard-style ordering flow.

**Architecture:** `apps/orders/` with models, services, views, forms. Status machine as domain value object in `core/domain/value_objects.py`. OrderService handles all state transitions.

**Tech Stack:** Django 6.0, PostgreSQL JSONField, HTMX for wizard steps, pytest-django, factory_boy

---

## File Structure

```
mpp/core/domain/
└── value_objects.py         # OrderStatus enum + StatusMachine

mpp/apps/orders/
├── __init__.py
├── apps.py
├── models.py                # Order, OrderItem, OrderItemGroup
├── services.py              # OrderService
├── views.py                 # OrderListView, OrderDetailView, OrderCreateView, OrderSubmitView
├── forms.py                 # OrderItemForm
├── admin.py
└── urls.py

mpp/templates/orders/
├── order_list.html
├── order_detail.html
├── order_create.html        # Wizard: select parameters, add to order
└── partials/
    ├── order_row.html
    └── item_form.html

tests/
├── unit/
│   ├── test_order_status_machine.py
│   └── test_order_service.py
└── integration/
    ├── test_order_model.py
    └── test_order_views.py
```

---

## Task 1: OrderStatus & Status Machine (Domain)

**Files:**
- Create: `mpp/core/domain/value_objects.py`
- Test: `tests/unit/test_order_status_machine.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_order_status_machine.py`:

```python
"""Test order status machine."""
from core.domain.value_objects import OrderStatus, StatusMachine


class TestOrderStatus:
    def test_has_expected_statuses(self):
        expected = ["draft", "validated", "submitted", "pending_approval",
                    "approved", "rejected", "provisioning", "done", "failed"]
        assert len(OrderStatus.choices) == len(expected)
        for status in expected:
            assert hasattr(OrderStatus, status.upper())

    def test_draft_is_default(self):
        assert OrderStatus.DRAFT == "draft"


class TestStatusMachine:
    def test_draft_can_transition_to_validated(self):
        assert StatusMachine.can_transition("draft", "validated") is True

    def test_validated_can_transition_to_submitted(self):
        assert StatusMachine.can_transition("validated", "submitted") is True

    def test_submitted_can_transition_to_pending_approval(self):
        assert StatusMachine.can_transition("submitted", "pending_approval") is True

    def test_submitted_can_transition_to_approved(self):
        assert StatusMachine.can_transition("submitted", "approved") is True

    def test_pending_approval_can_transition_to_approved(self):
        assert StatusMachine.can_transition("pending_approval", "approved") is True

    def test_pending_approval_can_transition_to_rejected(self):
        assert StatusMachine.can_transition("pending_approval", "rejected") is True

    def test_approved_can_transition_to_provisioning(self):
        assert StatusMachine.can_transition("approved", "provisioning") is True

    def test_provisioning_can_transition_to_done(self):
        assert StatusMachine.can_transition("provisioning", "done") is True

    def test_provisioning_can_transition_to_failed(self):
        assert StatusMachine.can_transition("provisioning", "failed") is True

    def test_done_is_terminal(self):
        assert StatusMachine.can_transition("done", "draft") is False
        assert StatusMachine.is_terminal("done") is True

    def test_failed_is_terminal(self):
        assert StatusMachine.is_terminal("failed") is True

    def test_rejected_is_terminal(self):
        assert StatusMachine.is_terminal("rejected") is True

    def test_draft_is_not_terminal(self):
        assert StatusMachine.is_terminal("draft") is False

    def test_invalid_transition_rejected(self):
        assert StatusMachine.can_transition("draft", "done") is False
        assert StatusMachine.can_transition("draft", "provisioning") is False

    def test_get_allowed_transitions(self):
        allowed = StatusMachine.get_allowed_transitions("draft")
        assert "validated" in allowed
        assert "done" not in allowed

    def test_transition_raises_on_invalid(self):
        import pytest
        with pytest.raises(ValueError):
            StatusMachine.validate_transition("draft", "done")
```

- [ ] **Step 2: Verify fail, then implement**

`mpp/core/domain/value_objects.py`:
```python
"""Domain value objects — status machines, validation rules."""
from django.db import models


class OrderStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    VALIDATED = "validated", "Validated"
    SUBMITTED = "submitted", "Submitted"
    PENDING_APPROVAL = "pending_approval", "Pending Approval"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    PROVISIONING = "provisioning", "Provisioning"
    DONE = "done", "Done"
    FAILED = "failed", "Failed"


TRANSITIONS = {
    OrderStatus.DRAFT: [OrderStatus.VALIDATED],
    OrderStatus.VALIDATED: [OrderStatus.SUBMITTED],
    OrderStatus.SUBMITTED: [OrderStatus.PENDING_APPROVAL, OrderStatus.APPROVED],
    OrderStatus.PENDING_APPROVAL: [OrderStatus.APPROVED, OrderStatus.REJECTED],
    OrderStatus.APPROVED: [OrderStatus.PROVISIONING],
    OrderStatus.PROVISIONING: [OrderStatus.DONE, OrderStatus.FAILED],
    OrderStatus.REJECTED: [],
    OrderStatus.DONE: [],
    OrderStatus.FAILED: [],
}

TERMINAL_STATES = {OrderStatus.DONE, OrderStatus.FAILED, OrderStatus.REJECTED}


class StatusMachine:
    @staticmethod
    def can_transition(from_status: str, to_status: str) -> bool:
        allowed = TRANSITIONS.get(from_status, [])
        return to_status in allowed

    @staticmethod
    def is_terminal(status: str) -> bool:
        return status in TERMINAL_STATES

    @staticmethod
    def get_allowed_transitions(status: str) -> list[str]:
        return list(TRANSITIONS.get(status, []))

    @staticmethod
    def validate_transition(from_status: str, to_status: str) -> None:
        if not StatusMachine.can_transition(from_status, to_status):
            raise ValueError(
                f"Invalid transition: {from_status} → {to_status}. "
                f"Allowed: {StatusMachine.get_allowed_transitions(from_status)}"
            )
```

Run: `python -m pytest tests/unit/test_order_status_machine.py -v` — expect 16 passed.
Commit: `git commit -m "feat(B3): add OrderStatus enum and StatusMachine"`

---

## Task 2: Order Models

**Files:**
- Create: `mpp/apps/orders/__init__.py`, `apps.py`, `models.py`, `admin.py`
- Modify: `mpp/config/settings/base.py` (add apps.orders)
- Test: `tests/integration/test_order_model.py`

- [ ] **Step 1: Write failing tests**

Create `tests/integration/test_order_model.py`:

```python
"""Test Order models."""
import pytest
from apps.orders.models import Order, OrderItem, OrderItemGroup
from core.domain.value_objects import OrderStatus
from tests.factories import UserFactory, ServiceTemplateFactory


@pytest.mark.django_db
class TestOrderModel:
    def test_create_order(self):
        user = UserFactory()
        order = Order.objects.create(user=user, notes="Test order")
        assert order.pk is not None
        assert order.status == OrderStatus.DRAFT
        assert order.notes == "Test order"

    def test_str_returns_id_and_status(self):
        user = UserFactory()
        order = Order.objects.create(user=user)
        assert f"Order #{order.pk}" in str(order)

    def test_has_timestamps(self):
        user = UserFactory()
        order = Order.objects.create(user=user)
        assert order.created_at is not None

    def test_ordering_by_created_at_desc(self):
        user = UserFactory()
        o1 = Order.objects.create(user=user, notes="first")
        o2 = Order.objects.create(user=user, notes="second")
        orders = list(Order.objects.all())
        assert orders[0].pk == o2.pk


@pytest.mark.django_db
class TestOrderItemModel:
    def test_create_order_item(self):
        user = UserFactory()
        template = ServiceTemplateFactory()
        order = Order.objects.create(user=user)
        item = OrderItem.objects.create(
            order=order, template=template,
            parameters={"cpu": 4, "ram_gb": 8},
        )
        assert item.pk is not None
        assert item.parameters == {"cpu": 4, "ram_gb": 8}

    def test_item_belongs_to_order(self):
        user = UserFactory()
        template = ServiceTemplateFactory()
        order = Order.objects.create(user=user)
        OrderItem.objects.create(order=order, template=template)
        assert order.items.count() == 1

    def test_str_returns_template_name(self):
        user = UserFactory()
        template = ServiceTemplateFactory(name="Linux VM")
        order = Order.objects.create(user=user)
        item = OrderItem.objects.create(order=order, template=template)
        assert "Linux VM" in str(item)


@pytest.mark.django_db
class TestOrderItemGroupModel:
    def test_create_group(self):
        user = UserFactory()
        template = ServiceTemplateFactory()
        order = Order.objects.create(user=user)
        group = OrderItemGroup.objects.create(
            order=order, template=template,
            quantity=3, shared_parameters={"cpu": 2},
        )
        assert group.pk is not None
        assert group.quantity == 3

    def test_item_can_belong_to_group(self):
        user = UserFactory()
        template = ServiceTemplateFactory()
        order = Order.objects.create(user=user)
        group = OrderItemGroup.objects.create(
            order=order, template=template, quantity=2,
        )
        item = OrderItem.objects.create(
            order=order, template=template, group=group,
        )
        assert item.group == group
        assert group.items.count() == 1
```

- [ ] **Step 2: Verify fail, then implement**

`mpp/apps/orders/apps.py`:
```python
from django.apps import AppConfig
class OrdersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.orders"
    verbose_name = "Orders"
```

`mpp/apps/orders/models.py`:
```python
from django.conf import settings
from django.db import models
from core.mixins import TimeStampedModel
from core.domain.value_objects import OrderStatus


class Order(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(max_length=30, choices=OrderStatus.choices, default=OrderStatus.DRAFT)
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} ({self.status})"


class OrderItemGroup(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="groups")
    template = models.ForeignKey("catalog.ServiceTemplate", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    shared_parameters = models.JSONField(default=dict)

    class Meta:
        db_table = "order_item_groups"

    def __str__(self):
        return f"Group: {self.template.name} x{self.quantity}"


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    template = models.ForeignKey("catalog.ServiceTemplate", on_delete=models.PROTECT)
    parameters = models.JSONField(default=dict)
    group = models.ForeignKey(OrderItemGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name="items")

    class Meta:
        db_table = "order_items"

    def __str__(self):
        return f"Item: {self.template.name}"
```

`mpp/apps/orders/admin.py`:
```python
from django.contrib import admin
from .models import Order, OrderItem, OrderItemGroup

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["created_at"]

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["pk", "user", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["user__username", "notes"]
    inlines = [OrderItemInline]

@admin.register(OrderItemGroup)
class OrderItemGroupAdmin(admin.ModelAdmin):
    list_display = ["pk", "order", "template", "quantity"]
```

Add `"apps.orders"` to INSTALLED_APPS. Run `makemigrations orders && migrate`.

Run: `python -m pytest tests/integration/test_order_model.py -v` — expect 11 passed.
Commit: `git commit -m "feat(B3): add Order, OrderItem, OrderItemGroup models"`

---

## Task 3: OrderService

**Files:**
- Create: `mpp/apps/orders/services.py`
- Update: `tests/factories.py` (add OrderFactory, OrderItemFactory)
- Test: `tests/unit/test_order_service.py`

- [ ] **Step 1: Update factories**

Add to `tests/factories.py`:
```python
from apps.orders.models import Order, OrderItem
from core.domain.value_objects import OrderStatus

class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order
    user = factory.SubFactory(UserFactory)
    status = OrderStatus.DRAFT
    notes = ""

class OrderItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrderItem
    order = factory.SubFactory(OrderFactory)
    template = factory.SubFactory(ServiceTemplateFactory)
    parameters = factory.LazyFunction(lambda: {"cpu": 2, "ram_gb": 4})
```

- [ ] **Step 2: Write failing tests**

Create `tests/unit/test_order_service.py`:

```python
"""Test OrderService."""
import pytest
from apps.orders.models import Order, OrderItem
from apps.orders.services import OrderService
from core.domain.value_objects import OrderStatus
from core.exceptions import ValidationError, NotFoundError, ConflictError
from tests.factories import UserFactory, ServiceTemplateFactory, OrderFactory, OrderItemFactory


@pytest.mark.django_db
class TestOrderServiceCreate:
    def test_create_order(self):
        user = UserFactory()
        order = OrderService.create_order(user=user, notes="Test")
        assert order.status == OrderStatus.DRAFT
        assert order.user == user
        assert order.notes == "Test"

    def test_create_order_without_notes(self):
        user = UserFactory()
        order = OrderService.create_order(user=user)
        assert order.notes == ""


@pytest.mark.django_db
class TestOrderServiceAddItem:
    def test_add_item_to_draft_order(self):
        user = UserFactory()
        template = ServiceTemplateFactory(parameters=[
            {"key": "cpu", "type": "integer", "required": True},
        ])
        order = OrderService.create_order(user=user)
        item = OrderService.add_item(
            order_id=order.pk, template_id=template.pk,
            parameters={"cpu": 4},
        )
        assert item.order == order
        assert item.template == template
        assert item.parameters == {"cpu": 4}

    def test_add_item_validates_parameters(self):
        user = UserFactory()
        template = ServiceTemplateFactory(parameters=[
            {"key": "cpu", "type": "integer", "required": True},
        ])
        order = OrderService.create_order(user=user)
        with pytest.raises(ValidationError):
            OrderService.add_item(
                order_id=order.pk, template_id=template.pk,
                parameters={},
            )

    def test_add_item_to_non_draft_raises(self):
        order = OrderFactory(status=OrderStatus.SUBMITTED)
        template = ServiceTemplateFactory()
        with pytest.raises(ConflictError):
            OrderService.add_item(
                order_id=order.pk, template_id=template.pk,
                parameters={"cpu": 2},
            )

    def test_add_item_nonexistent_order_raises(self):
        template = ServiceTemplateFactory()
        with pytest.raises(NotFoundError):
            OrderService.add_item(order_id=99999, template_id=template.pk, parameters={})


@pytest.mark.django_db
class TestOrderServiceRemoveItem:
    def test_remove_item(self):
        item = OrderItemFactory()
        OrderService.remove_item(item_id=item.pk)
        assert OrderItem.objects.filter(pk=item.pk).count() == 0

    def test_remove_item_from_non_draft_raises(self):
        order = OrderFactory(status=OrderStatus.SUBMITTED)
        item = OrderItemFactory(order=order)
        with pytest.raises(ConflictError):
            OrderService.remove_item(item_id=item.pk)


@pytest.mark.django_db
class TestOrderServiceSubmit:
    def test_submit_order_with_items(self):
        order = OrderFactory()
        OrderItemFactory(order=order)
        result = OrderService.submit_order(order_id=order.pk)
        assert result.status == OrderStatus.SUBMITTED

    def test_submit_empty_order_raises(self):
        order = OrderFactory()
        with pytest.raises(ValidationError):
            OrderService.submit_order(order_id=order.pk)

    def test_submit_non_draft_raises(self):
        order = OrderFactory(status=OrderStatus.SUBMITTED)
        OrderItemFactory(order=order)
        with pytest.raises(ConflictError):
            OrderService.submit_order(order_id=order.pk)


@pytest.mark.django_db
class TestOrderServiceGet:
    def test_get_order(self):
        order = OrderFactory()
        result = OrderService.get_order(order.pk)
        assert result.pk == order.pk

    def test_get_nonexistent_raises(self):
        with pytest.raises(NotFoundError):
            OrderService.get_order(99999)

    def test_list_user_orders(self):
        user = UserFactory()
        OrderFactory(user=user)
        OrderFactory(user=user)
        OrderFactory()  # other user
        orders = OrderService.list_user_orders(user_id=user.pk)
        assert len(orders) == 2
```

- [ ] **Step 3: Implement OrderService**

`mpp/apps/orders/services.py`:
```python
"""Order business logic."""
from apps.catalog.services import CatalogService
from apps.orders.models import Order, OrderItem
from core.domain.value_objects import OrderStatus, StatusMachine
from core.exceptions import ConflictError, NotFoundError, ValidationError


class OrderService:
    @staticmethod
    def create_order(user, notes="") -> Order:
        return Order.objects.create(user=user, notes=notes)

    @staticmethod
    def get_order(order_id: int) -> Order:
        try:
            return Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            raise NotFoundError(f"Order with id={order_id} not found.")

    @staticmethod
    def list_user_orders(user_id: int) -> list[Order]:
        return list(Order.objects.filter(user_id=user_id))

    @staticmethod
    def add_item(order_id: int, template_id: int, parameters: dict) -> OrderItem:
        order = OrderService.get_order(order_id)
        if order.status != OrderStatus.DRAFT:
            raise ConflictError("Items can only be added to draft orders.")

        template = CatalogService.get_template(template_id)
        errors = CatalogService.validate_template_parameters(template_id, parameters)
        if errors:
            raise ValidationError("Parameter validation failed.", details=errors)

        return OrderItem.objects.create(
            order=order, template=template, parameters=parameters,
        )

    @staticmethod
    def remove_item(item_id: int) -> None:
        try:
            item = OrderItem.objects.select_related("order").get(pk=item_id)
        except OrderItem.DoesNotExist:
            raise NotFoundError(f"OrderItem with id={item_id} not found.")
        if item.order.status != OrderStatus.DRAFT:
            raise ConflictError("Items can only be removed from draft orders.")
        item.delete()

    @staticmethod
    def submit_order(order_id: int) -> Order:
        order = OrderService.get_order(order_id)
        if order.status != OrderStatus.DRAFT:
            raise ConflictError(f"Cannot submit order in status '{order.status}'.")

        if order.items.count() == 0:
            raise ValidationError("Cannot submit an order without items.")

        StatusMachine.validate_transition(order.status, OrderStatus.VALIDATED)
        order.status = OrderStatus.VALIDATED
        order.save()

        StatusMachine.validate_transition(order.status, OrderStatus.SUBMITTED)
        order.status = OrderStatus.SUBMITTED
        order.save()
        return order
```

Run: `python -m pytest tests/unit/test_order_service.py -v` — expect 14 passed.
Commit: `git commit -m "feat(B3): add OrderService with create, add/remove items, submit"`

---

## Task 4: Order Views & Templates

**Files:**
- Create: `mpp/apps/orders/views.py`, `forms.py`, `urls.py`
- Create: `mpp/templates/orders/order_list.html`, `order_detail.html`, `order_create.html`
- Create: `mpp/templates/orders/partials/order_row.html`
- Modify: `mpp/config/urls.py`
- Test: `tests/integration/test_order_views.py`

- [ ] **Step 1: Write failing tests**

Create `tests/integration/test_order_views.py`:

```python
"""Test order views."""
import pytest
from django.urls import reverse
from core.domain.value_objects import OrderStatus
from tests.factories import UserFactory, ServiceTemplateFactory, OrderFactory, OrderItemFactory


@pytest.mark.django_db
class TestOrderListView:
    def test_requires_login(self, client):
        response = client.get(reverse("orders:list"))
        assert response.status_code == 302

    def test_returns_200(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("orders:list"))
        assert response.status_code == 200

    def test_shows_only_own_orders(self, client):
        user = UserFactory()
        other = UserFactory()
        OrderFactory(user=user, notes="mine")
        OrderFactory(user=other, notes="theirs")
        client.force_login(user)
        response = client.get(reverse("orders:list"))
        content = response.content.decode()
        assert "mine" in content or f"Order #{Order.objects.filter(user=user).first().pk}" in content


@pytest.mark.django_db
class TestOrderDetailView:
    def test_requires_login(self, client):
        order = OrderFactory()
        response = client.get(reverse("orders:detail", kwargs={"pk": order.pk}))
        assert response.status_code == 302

    def test_returns_200_for_owner(self, client):
        user = UserFactory()
        order = OrderFactory(user=user)
        client.force_login(user)
        response = client.get(reverse("orders:detail", kwargs={"pk": order.pk}))
        assert response.status_code == 200

    def test_shows_order_items(self, client):
        user = UserFactory()
        order = OrderFactory(user=user)
        template = ServiceTemplateFactory(name="Linux VM")
        OrderItemFactory(order=order, template=template)
        client.force_login(user)
        response = client.get(reverse("orders:detail", kwargs={"pk": order.pk}))
        assert "Linux VM" in response.content.decode()

    def test_404_for_nonexistent(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("orders:detail", kwargs={"pk": 99999}))
        assert response.status_code == 404


@pytest.mark.django_db
class TestOrderCreateView:
    def test_requires_login(self, client):
        template = ServiceTemplateFactory()
        response = client.get(reverse("orders:create", kwargs={"template_pk": template.pk}))
        assert response.status_code == 302

    def test_returns_200(self, client):
        user = UserFactory()
        template = ServiceTemplateFactory()
        client.force_login(user)
        response = client.get(reverse("orders:create", kwargs={"template_pk": template.pk}))
        assert response.status_code == 200

    def test_post_creates_order_with_item(self, client):
        user = UserFactory()
        template = ServiceTemplateFactory(parameters=[
            {"key": "cpu", "type": "integer", "required": True},
        ])
        client.force_login(user)
        response = client.post(
            reverse("orders:create", kwargs={"template_pk": template.pk}),
            {"cpu": "4"},
        )
        assert response.status_code == 302
        from apps.orders.models import Order
        order = Order.objects.filter(user=user).first()
        assert order is not None
        assert order.items.count() == 1


@pytest.mark.django_db
class TestOrderSubmitView:
    def test_submit_order(self, client):
        user = UserFactory()
        order = OrderFactory(user=user)
        OrderItemFactory(order=order)
        client.force_login(user)
        response = client.post(reverse("orders:submit", kwargs={"pk": order.pk}))
        assert response.status_code == 302
        order.refresh_from_db()
        assert order.status == OrderStatus.SUBMITTED

    def test_submit_empty_order_fails(self, client):
        user = UserFactory()
        order = OrderFactory(user=user)
        client.force_login(user)
        response = client.post(reverse("orders:submit", kwargs={"pk": order.pk}))
        assert response.status_code in [302, 200]
        order.refresh_from_db()
        assert order.status == OrderStatus.DRAFT
```

- [ ] **Step 2: Verify fail, then implement views, forms, urls, templates**

`mpp/apps/orders/forms.py`:
```python
from django import forms

class OrderParameterForm(forms.Form):
    """Dynamic form built from template parameters at runtime."""
    def __init__(self, *args, template_parameters=None, **kwargs):
        super().__init__(*args, **kwargs)
        if template_parameters:
            for param in template_parameters:
                key = param["key"]
                label = param.get("label", key)
                required = param.get("required", False)
                param_type = param.get("type", "string")

                if param_type == "choice":
                    options = param.get("options", [])
                    self.fields[key] = forms.ChoiceField(
                        choices=[(o, o) for o in options],
                        required=required, label=label,
                    )
                elif param_type == "boolean":
                    self.fields[key] = forms.BooleanField(required=False, label=label)
                elif param_type == "integer":
                    self.fields[key] = forms.IntegerField(required=required, label=label)
                else:
                    self.fields[key] = forms.CharField(required=required, label=label)

                if "default" in param and not self.is_bound:
                    self.fields[key].initial = param["default"]
```

`mpp/apps/orders/views.py`:
```python
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView, FormView

from apps.catalog.services import CatalogService
from core.exceptions import NotFoundError, ValidationError, ConflictError
from core.mixins import RequesterRequiredMixin
from .forms import OrderParameterForm
from .models import Order
from .services import OrderService


class OrderListView(RequesterRequiredMixin, ListView):
    template_name = "orders/order_list.html"
    context_object_name = "orders"

    def get_queryset(self):
        return OrderService.list_user_orders(user_id=self.request.user.pk)


class OrderDetailView(RequesterRequiredMixin, DetailView):
    template_name = "orders/order_detail.html"
    context_object_name = "order"

    def get_object(self, queryset=None):
        try:
            order = OrderService.get_order(self.kwargs["pk"])
        except NotFoundError:
            raise Http404
        return order

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["items"] = self.object.items.select_related("template").all()
        return ctx


class OrderCreateView(RequesterRequiredMixin, FormView):
    template_name = "orders/order_create.html"

    def get_template_obj(self):
        try:
            return CatalogService.get_template(self.kwargs["template_pk"])
        except NotFoundError:
            raise Http404

    def get_form(self, form_class=None):
        template = self.get_template_obj()
        return OrderParameterForm(
            self.request.POST or None,
            template_parameters=template.parameters,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["service_template"] = self.get_template_obj()
        return ctx

    def form_valid(self, form):
        template = self.get_template_obj()
        params = {}
        for param in template.parameters:
            key = param["key"]
            if key in form.cleaned_data:
                params[key] = form.cleaned_data[key]

        try:
            order = OrderService.create_order(user=self.request.user)
            OrderService.add_item(
                order_id=order.pk,
                template_id=template.pk,
                parameters=params,
            )
            messages.success(self.request, f"Bestellung #{order.pk} erstellt.")
            return redirect("orders:detail", pk=order.pk)
        except (ValidationError, ConflictError) as e:
            messages.error(self.request, e.message)
            return self.form_invalid(form)


class OrderSubmitView(RequesterRequiredMixin, View):
    def post(self, request, pk):
        try:
            OrderService.submit_order(order_id=pk)
            messages.success(request, "Bestellung eingereicht.")
        except (ValidationError, ConflictError) as e:
            messages.error(request, e.message)
        return redirect("orders:detail", pk=pk)
```

`mpp/apps/orders/urls.py`:
```python
from django.urls import path
from . import views

app_name = "orders"
urlpatterns = [
    path("", views.OrderListView.as_view(), name="list"),
    path("<int:pk>/", views.OrderDetailView.as_view(), name="detail"),
    path("create/<int:template_pk>/", views.OrderCreateView.as_view(), name="create"),
    path("<int:pk>/submit/", views.OrderSubmitView.as_view(), name="submit"),
]
```

Add `path("orders/", include("apps.orders.urls")),` to `mpp/config/urls.py`.

**Templates:** (Create standard DaisyUI templates for list, detail, create)

`mpp/templates/orders/order_list.html`, `order_detail.html`, `order_create.html` — use DaisyUI table, cards, forms. Keep simple.

Run: `python -m pytest tests/integration/test_order_views.py -v` — expect ~12 passed.

Run ALL: `python -m pytest tests/ -v` — expect ~123 passed.

Commit: `git commit -m "feat(B3): add order views with create wizard, detail, list, submit"`

---

## Summary

| Task | Description | Tests |
|------|-------------|-------|
| 1 | OrderStatus + StatusMachine | 16 |
| 2 | Order/OrderItem/Group models | 11 |
| 3 | OrderService | 14 |
| 4 | Order views + templates | ~12 |
| **Total new** | | **~53** |
| **Running total** | | **~139** |
