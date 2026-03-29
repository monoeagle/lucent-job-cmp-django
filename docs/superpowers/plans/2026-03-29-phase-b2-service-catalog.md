# Phase B2: Service Catalog — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the Service Catalog — templates for VMs, databases, and containers with parametric JSON schemas, validation, search/filter, and CRUD views.

**Architecture:** Hybrid pattern — `apps/catalog/` with models.py, services.py, views.py, forms.py, admin.py. Templates with HTMX for search/filter. Django Admin for template management (admin+ roles). Public catalog browsing for all authenticated users.

**Tech Stack:** Django 6.0, PostgreSQL JSONField, pytest-django, factory_boy, HTMX

---

## File Structure

```
mpp/apps/catalog/
├── __init__.py
├── apps.py
├── models.py          # ServiceTemplate with JSONField parameters
├── services.py        # CatalogService (list, search, validate)
├── views.py           # TemplateListView, TemplateDetailView
├── forms.py           # TemplateFilterForm
├── admin.py           # ServiceTemplateAdmin
├── urls.py
└── templatetags/
    ├── __init__.py
    └── catalog_tags.py  # Custom tags for parameter rendering

mpp/templates/catalog/
├── template_list.html
├── template_detail.html
└── partials/
    └── template_grid.html    # HTMX partial for search results

tests/
├── unit/
│   ├── test_catalog_domain.py
│   └── test_catalog_service.py
└── integration/
    ├── test_catalog_model.py
    └── test_catalog_views.py
```

---

## Task 1: ServiceTemplate Model

**Files:**
- Create: `mpp/apps/catalog/__init__.py`, `apps.py`, `models.py`
- Create: `mpp/apps/catalog/admin.py`
- Modify: `mpp/config/settings/base.py` (add apps.catalog)
- Test: `tests/integration/test_catalog_model.py`

- [ ] **Step 1: Write failing tests**

Create `tests/integration/test_catalog_model.py`:

```python
"""Test ServiceTemplate model."""
import pytest
from apps.catalog.models import ServiceTemplate


@pytest.mark.django_db
class TestServiceTemplateModel:
    def test_create_template(self):
        t = ServiceTemplate.objects.create(
            name="Linux VM",
            category="compute",
            description="Standard Linux Virtual Machine",
            parameters=[
                {"key": "cpu", "type": "integer", "label": "CPUs", "required": True, "default": 2},
                {"key": "ram_gb", "type": "integer", "label": "RAM (GB)", "required": True, "default": 4},
            ],
        )
        assert t.pk is not None
        assert t.is_active is True
        assert t.version == 1

    def test_str_returns_name(self):
        t = ServiceTemplate.objects.create(name="PostgreSQL DB", category="database")
        assert str(t) == "PostgreSQL DB"

    def test_has_timestamps(self):
        t = ServiceTemplate.objects.create(name="Test", category="test")
        assert t.created_at is not None
        assert t.updated_at is not None

    def test_default_parameters_is_empty_list(self):
        t = ServiceTemplate.objects.create(name="Empty", category="test")
        assert t.parameters == []

    def test_ordering_by_name(self):
        ServiceTemplate.objects.create(name="Zebra", category="test")
        ServiceTemplate.objects.create(name="Alpha", category="test")
        templates = list(ServiceTemplate.objects.values_list("name", flat=True))
        assert templates == ["Alpha", "Zebra"]

    def test_category_choices(self):
        for cat in ["compute", "database", "container", "network", "storage"]:
            t = ServiceTemplate.objects.create(name=f"Test-{cat}", category=cat)
            assert t.category == cat
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `python -m pytest tests/integration/test_catalog_model.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implement ServiceTemplate model**

`mpp/apps/catalog/__init__.py`: empty

`mpp/apps/catalog/apps.py`:
```python
from django.apps import AppConfig

class CatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.catalog"
    verbose_name = "Service Catalog"
```

`mpp/apps/catalog/models.py`:
```python
"""Service catalog models."""
from django.db import models
from core.mixins import TimeStampedModel


class TemplateCategory(models.TextChoices):
    COMPUTE = "compute", "Compute"
    DATABASE = "database", "Database"
    CONTAINER = "container", "Container"
    NETWORK = "network", "Network"
    STORAGE = "storage", "Storage"


class ServiceTemplate(TimeStampedModel):
    """A service template in the catalog."""
    name = models.CharField(max_length=200, unique=True)
    category = models.CharField(max_length=30, choices=TemplateCategory.choices)
    description = models.TextField(blank=True, default="")
    parameters = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "service_templates"
        ordering = ["name"]

    def __str__(self):
        return self.name
```

- [ ] **Step 4: Register in settings, create migration**

Add `"apps.catalog"` to INSTALLED_APPS in `mpp/config/settings/base.py`.

Run:
```bash
cd mpp && python manage.py makemigrations catalog && python manage.py migrate
```

- [ ] **Step 5: Create admin.py**

`mpp/apps/catalog/admin.py`:
```python
from django.contrib import admin
from .models import ServiceTemplate

@admin.register(ServiceTemplate)
class ServiceTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "is_active", "version", "created_at"]
    list_filter = ["category", "is_active"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]
```

- [ ] **Step 6: Run tests — verify they pass**

Run: `python -m pytest tests/integration/test_catalog_model.py -v`
Expected: 6 passed.

- [ ] **Step 7: Commit**

```bash
git add mpp/apps/catalog/ mpp/config/settings/base.py tests/integration/test_catalog_model.py
git commit -m "feat(B2): add ServiceTemplate model with JSONField parameters"
```

---

## Task 2: Template Validator (Domain Logic)

**Files:**
- Create: `mpp/core/domain/validators.py`
- Test: `tests/unit/test_catalog_domain.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_catalog_domain.py`:

```python
"""Test catalog domain logic — template parameter validation."""
import pytest
from core.domain.validators import TemplateValidator


class TestTemplateValidator:
    def test_valid_parameters_pass(self):
        schema = [
            {"key": "cpu", "type": "integer", "required": True, "default": 2},
            {"key": "ram_gb", "type": "integer", "required": True, "default": 4},
        ]
        values = {"cpu": 4, "ram_gb": 8}
        errors = TemplateValidator.validate_parameters(schema, values)
        assert errors == []

    def test_missing_required_parameter(self):
        schema = [
            {"key": "cpu", "type": "integer", "required": True},
        ]
        values = {}
        errors = TemplateValidator.validate_parameters(schema, values)
        assert len(errors) == 1
        assert errors[0]["key"] == "cpu"
        assert "required" in errors[0]["message"].lower()

    def test_optional_parameter_can_be_missing(self):
        schema = [
            {"key": "notes", "type": "string", "required": False},
        ]
        values = {}
        errors = TemplateValidator.validate_parameters(schema, values)
        assert errors == []

    def test_wrong_type_integer(self):
        schema = [
            {"key": "cpu", "type": "integer", "required": True},
        ]
        values = {"cpu": "not-a-number"}
        errors = TemplateValidator.validate_parameters(schema, values)
        assert len(errors) == 1
        assert "type" in errors[0]["message"].lower()

    def test_wrong_type_string(self):
        schema = [
            {"key": "name", "type": "string", "required": True},
        ]
        values = {"name": 123}
        errors = TemplateValidator.validate_parameters(schema, values)
        assert len(errors) == 1

    def test_unknown_parameter_ignored(self):
        schema = [
            {"key": "cpu", "type": "integer", "required": True},
        ]
        values = {"cpu": 4, "unknown": "value"}
        errors = TemplateValidator.validate_parameters(schema, values)
        assert errors == []

    def test_empty_schema_accepts_any(self):
        errors = TemplateValidator.validate_parameters([], {"anything": "goes"})
        assert errors == []

    def test_schema_must_have_at_least_key_and_type(self):
        schema = [{"key": "cpu"}]  # missing type
        values = {"cpu": 4}
        errors = TemplateValidator.validate_parameters(schema, values)
        assert len(errors) == 1
        assert "type" in errors[0]["message"].lower()

    def test_boolean_type_validation(self):
        schema = [{"key": "ha", "type": "boolean", "required": True}]
        values = {"ha": True}
        errors = TemplateValidator.validate_parameters(schema, values)
        assert errors == []

    def test_boolean_type_rejects_string(self):
        schema = [{"key": "ha", "type": "boolean", "required": True}]
        values = {"ha": "yes"}
        errors = TemplateValidator.validate_parameters(schema, values)
        assert len(errors) == 1

    def test_choice_type_validation(self):
        schema = [{"key": "size", "type": "choice", "required": True, "options": ["s", "m", "l"]}]
        values = {"size": "m"}
        errors = TemplateValidator.validate_parameters(schema, values)
        assert errors == []

    def test_choice_type_rejects_invalid(self):
        schema = [{"key": "size", "type": "choice", "required": True, "options": ["s", "m", "l"]}]
        values = {"size": "xl"}
        errors = TemplateValidator.validate_parameters(schema, values)
        assert len(errors) == 1
        assert "options" in errors[0]["message"].lower() or "choice" in errors[0]["message"].lower()
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `python -m pytest tests/unit/test_catalog_domain.py -v`

- [ ] **Step 3: Implement TemplateValidator**

`mpp/core/domain/validators.py`:
```python
"""Domain validators — no Django dependencies."""

TYPE_CHECKS = {
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "string": lambda v: isinstance(v, str),
    "boolean": lambda v: isinstance(v, bool),
    "float": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
}


class TemplateValidator:
    @staticmethod
    def validate_parameters(schema: list[dict], values: dict) -> list[dict]:
        """Validate parameter values against a template schema.

        Returns list of error dicts: [{"key": str, "message": str}]
        """
        errors = []

        for param in schema:
            key = param.get("key")
            param_type = param.get("type")

            if not param_type:
                errors.append({"key": key or "unknown", "message": "Parameter schema missing 'type' field."})
                continue

            value = values.get(key)
            required = param.get("required", False)

            if value is None:
                if required:
                    errors.append({"key": key, "message": f"Required parameter '{key}' is missing."})
                continue

            if param_type == "choice":
                options = param.get("options", [])
                if value not in options:
                    errors.append({"key": key, "message": f"Value must be one of the allowed options: {options}"})
            elif param_type in TYPE_CHECKS:
                if not TYPE_CHECKS[param_type](value):
                    errors.append({"key": key, "message": f"Expected type '{param_type}', got '{type(value).__name__}'."})

        return errors
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `python -m pytest tests/unit/test_catalog_domain.py -v`
Expected: 12 passed.

- [ ] **Step 5: Commit**

```bash
git add mpp/core/domain/validators.py tests/unit/test_catalog_domain.py
git commit -m "feat(B2): add TemplateValidator for parameter schema validation"
```

---

## Task 3: CatalogService

**Files:**
- Create: `mpp/apps/catalog/services.py`
- Create: `tests/factories.py` update (add ServiceTemplateFactory)
- Test: `tests/unit/test_catalog_service.py`

- [ ] **Step 1: Update factories.py**

Add to `tests/factories.py`:

```python
from apps.catalog.models import ServiceTemplate

class ServiceTemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ServiceTemplate

    name = factory.Sequence(lambda n: f"Template-{n}")
    category = "compute"
    description = factory.LazyAttribute(lambda o: f"Description for {o.name}")
    is_active = True
    version = 1
    parameters = factory.LazyFunction(lambda: [
        {"key": "cpu", "type": "integer", "label": "CPUs", "required": True, "default": 2},
        {"key": "ram_gb", "type": "integer", "label": "RAM (GB)", "required": True, "default": 4},
    ])
```

- [ ] **Step 2: Write failing tests**

Create `tests/unit/test_catalog_service.py`:

```python
"""Test CatalogService."""
import pytest
from apps.catalog.services import CatalogService
from apps.catalog.models import ServiceTemplate
from core.exceptions import NotFoundError, ValidationError
from tests.factories import ServiceTemplateFactory


@pytest.mark.django_db
class TestCatalogServiceList:
    def test_list_active_templates(self):
        ServiceTemplateFactory(name="Active", is_active=True)
        ServiceTemplateFactory(name="Inactive", is_active=False)
        templates = CatalogService.list_active_templates()
        assert len(templates) == 1
        assert templates[0].name == "Active"

    def test_list_active_returns_empty_when_none(self):
        templates = CatalogService.list_active_templates()
        assert len(templates) == 0

    def test_list_by_category(self):
        ServiceTemplateFactory(name="VM", category="compute")
        ServiceTemplateFactory(name="DB", category="database")
        templates = CatalogService.list_active_templates(category="compute")
        assert len(templates) == 1
        assert templates[0].name == "VM"

    def test_search_by_name(self):
        ServiceTemplateFactory(name="Linux VM Standard")
        ServiceTemplateFactory(name="PostgreSQL DB")
        templates = CatalogService.search_templates("linux")
        assert len(templates) == 1
        assert templates[0].name == "Linux VM Standard"

    def test_search_by_description(self):
        ServiceTemplateFactory(name="VM", description="High performance compute")
        ServiceTemplateFactory(name="DB", description="Managed database")
        templates = CatalogService.search_templates("performance")
        assert len(templates) == 1

    def test_search_is_case_insensitive(self):
        ServiceTemplateFactory(name="Linux VM")
        templates = CatalogService.search_templates("LINUX")
        assert len(templates) == 1


@pytest.mark.django_db
class TestCatalogServiceGet:
    def test_get_template_by_id(self):
        t = ServiceTemplateFactory(name="Test")
        result = CatalogService.get_template(t.pk)
        assert result.name == "Test"

    def test_get_nonexistent_raises_not_found(self):
        with pytest.raises(NotFoundError):
            CatalogService.get_template(99999)


@pytest.mark.django_db
class TestCatalogServiceValidate:
    def test_validate_valid_parameters(self):
        t = ServiceTemplateFactory(parameters=[
            {"key": "cpu", "type": "integer", "required": True},
        ])
        errors = CatalogService.validate_template_parameters(t.pk, {"cpu": 4})
        assert errors == []

    def test_validate_invalid_parameters(self):
        t = ServiceTemplateFactory(parameters=[
            {"key": "cpu", "type": "integer", "required": True},
        ])
        errors = CatalogService.validate_template_parameters(t.pk, {})
        assert len(errors) == 1

    def test_validate_nonexistent_template_raises(self):
        with pytest.raises(NotFoundError):
            CatalogService.validate_template_parameters(99999, {})


@pytest.mark.django_db
class TestCatalogServiceSeed:
    def test_seed_creates_three_templates(self):
        created = CatalogService.seed_templates()
        assert created == 3
        assert ServiceTemplate.objects.count() == 3

    def test_seed_is_idempotent(self):
        CatalogService.seed_templates()
        created = CatalogService.seed_templates()
        assert created == 0
```

- [ ] **Step 3: Run tests — verify they fail**

Run: `python -m pytest tests/unit/test_catalog_service.py -v`

- [ ] **Step 4: Implement CatalogService**

`mpp/apps/catalog/services.py`:
```python
"""Catalog business logic."""
from django.db.models import Q

from apps.catalog.models import ServiceTemplate
from core.domain.validators import TemplateValidator
from core.exceptions import NotFoundError

SEED_TEMPLATES = [
    {
        "name": "Linux VM",
        "category": "compute",
        "description": "Standard Linux Virtual Machine mit konfigurierbaren Ressourcen.",
        "parameters": [
            {"key": "cpu", "type": "integer", "label": "CPUs", "required": True, "default": 2},
            {"key": "ram_gb", "type": "integer", "label": "RAM (GB)", "required": True, "default": 4},
            {"key": "disk_gb", "type": "integer", "label": "Disk (GB)", "required": True, "default": 50},
            {"key": "os_version", "type": "choice", "label": "OS Version", "required": True,
             "options": ["ubuntu-22.04", "ubuntu-24.04", "debian-12", "rhel-9"], "default": "ubuntu-24.04"},
        ],
    },
    {
        "name": "Windows VM",
        "category": "compute",
        "description": "Windows Server Virtual Machine.",
        "parameters": [
            {"key": "cpu", "type": "integer", "label": "CPUs", "required": True, "default": 4},
            {"key": "ram_gb", "type": "integer", "label": "RAM (GB)", "required": True, "default": 8},
            {"key": "disk_gb", "type": "integer", "label": "Disk (GB)", "required": True, "default": 100},
            {"key": "os_version", "type": "choice", "label": "OS Version", "required": True,
             "options": ["win-server-2022", "win-server-2025"], "default": "win-server-2025"},
        ],
    },
    {
        "name": "PostgreSQL DB",
        "category": "database",
        "description": "Managed PostgreSQL Datenbank.",
        "parameters": [
            {"key": "version", "type": "choice", "label": "Version", "required": True,
             "options": ["14", "15", "16", "17"], "default": "16"},
            {"key": "storage_gb", "type": "integer", "label": "Storage (GB)", "required": True, "default": 20},
            {"key": "ha", "type": "boolean", "label": "High Availability", "required": False, "default": False},
        ],
    },
]


class CatalogService:
    @staticmethod
    def list_active_templates(category: str | None = None) -> list[ServiceTemplate]:
        qs = ServiceTemplate.objects.filter(is_active=True)
        if category:
            qs = qs.filter(category=category)
        return list(qs)

    @staticmethod
    def search_templates(query: str) -> list[ServiceTemplate]:
        return list(
            ServiceTemplate.objects.filter(
                Q(is_active=True) & (Q(name__icontains=query) | Q(description__icontains=query))
            )
        )

    @staticmethod
    def get_template(template_id: int) -> ServiceTemplate:
        try:
            return ServiceTemplate.objects.get(pk=template_id)
        except ServiceTemplate.DoesNotExist:
            raise NotFoundError(f"ServiceTemplate with id={template_id} not found.")

    @staticmethod
    def validate_template_parameters(template_id: int, values: dict) -> list[dict]:
        template = CatalogService.get_template(template_id)
        return TemplateValidator.validate_parameters(template.parameters, values)

    @staticmethod
    def seed_templates() -> int:
        created_count = 0
        for data in SEED_TEMPLATES:
            _, created = ServiceTemplate.objects.get_or_create(
                name=data["name"],
                defaults=data,
            )
            if created:
                created_count += 1
        return created_count
```

- [ ] **Step 5: Run tests — verify they pass**

Run: `python -m pytest tests/unit/test_catalog_service.py -v`
Expected: 13 passed.

- [ ] **Step 6: Commit**

```bash
git add mpp/apps/catalog/services.py tests/factories.py tests/unit/test_catalog_service.py
git commit -m "feat(B2): add CatalogService with list, search, validate, seed"
```

---

## Task 4: Catalog Views & Templates

**Files:**
- Create: `mpp/apps/catalog/views.py`
- Create: `mpp/apps/catalog/forms.py`
- Create: `mpp/apps/catalog/urls.py`
- Create: `mpp/templates/catalog/template_list.html`
- Create: `mpp/templates/catalog/template_detail.html`
- Create: `mpp/templates/catalog/partials/template_grid.html`
- Modify: `mpp/config/urls.py` (add catalog/)
- Test: `tests/integration/test_catalog_views.py`

- [ ] **Step 1: Write failing tests**

Create `tests/integration/test_catalog_views.py`:

```python
"""Test catalog views."""
import pytest
from django.urls import reverse
from tests.factories import UserFactory, ServiceTemplateFactory


@pytest.mark.django_db
class TestTemplateListView:
    def test_requires_login(self, client):
        response = client.get(reverse("catalog:list"))
        assert response.status_code == 302

    def test_returns_200(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("catalog:list"))
        assert response.status_code == 200

    def test_shows_active_templates(self, client):
        user = UserFactory()
        client.force_login(user)
        ServiceTemplateFactory(name="Linux VM", is_active=True)
        ServiceTemplateFactory(name="Hidden", is_active=False)
        response = client.get(reverse("catalog:list"))
        content = response.content.decode()
        assert "Linux VM" in content
        assert "Hidden" not in content

    def test_filter_by_category(self, client):
        user = UserFactory()
        client.force_login(user)
        ServiceTemplateFactory(name="VM", category="compute")
        ServiceTemplateFactory(name="DB", category="database")
        response = client.get(reverse("catalog:list") + "?category=compute")
        content = response.content.decode()
        assert "VM" in content
        assert "DB" not in content

    def test_search(self, client):
        user = UserFactory()
        client.force_login(user)
        ServiceTemplateFactory(name="Linux VM")
        ServiceTemplateFactory(name="PostgreSQL DB")
        response = client.get(reverse("catalog:list") + "?q=linux")
        content = response.content.decode()
        assert "Linux VM" in content
        assert "PostgreSQL DB" not in content

    def test_htmx_returns_partial(self, client):
        user = UserFactory()
        client.force_login(user)
        ServiceTemplateFactory(name="Linux VM")
        response = client.get(
            reverse("catalog:list"),
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestTemplateDetailView:
    def test_requires_login(self, client):
        t = ServiceTemplateFactory()
        response = client.get(reverse("catalog:detail", kwargs={"pk": t.pk}))
        assert response.status_code == 302

    def test_returns_200(self, client):
        user = UserFactory()
        client.force_login(user)
        t = ServiceTemplateFactory(name="Linux VM")
        response = client.get(reverse("catalog:detail", kwargs={"pk": t.pk}))
        assert response.status_code == 200
        assert "Linux VM" in response.content.decode()

    def test_shows_parameters(self, client):
        user = UserFactory()
        client.force_login(user)
        t = ServiceTemplateFactory(parameters=[
            {"key": "cpu", "type": "integer", "label": "CPUs", "required": True, "default": 2},
        ])
        response = client.get(reverse("catalog:detail", kwargs={"pk": t.pk}))
        assert "CPUs" in response.content.decode()

    def test_404_for_nonexistent(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("catalog:detail", kwargs={"pk": 99999}))
        assert response.status_code == 404
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `python -m pytest tests/integration/test_catalog_views.py -v`

- [ ] **Step 3: Implement views**

`mpp/apps/catalog/forms.py`:
```python
"""Catalog filter forms."""
from django import forms
from .models import TemplateCategory


class TemplateFilterForm(forms.Form):
    q = forms.CharField(required=False, label="Suche")
    category = forms.ChoiceField(
        required=False,
        choices=[("", "Alle Kategorien")] + TemplateCategory.choices,
        label="Kategorie",
    )
```

`mpp/apps/catalog/views.py`:
```python
"""Catalog views."""
from django.http import Http404
from django.views.generic import ListView, DetailView

from core.exceptions import NotFoundError
from core.mixins import RequesterRequiredMixin
from .models import ServiceTemplate
from .services import CatalogService
from .forms import TemplateFilterForm


class TemplateListView(RequesterRequiredMixin, ListView):
    model = ServiceTemplate
    template_name = "catalog/template_list.html"
    context_object_name = "templates"

    def get_queryset(self):
        category = self.request.GET.get("category")
        query = self.request.GET.get("q")
        if query:
            return CatalogService.search_templates(query)
        return CatalogService.list_active_templates(category=category or None)

    def get_template_names(self):
        if self.request.htmx:
            return ["catalog/partials/template_grid.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filter_form"] = TemplateFilterForm(self.request.GET)
        return ctx


class TemplateDetailView(RequesterRequiredMixin, DetailView):
    model = ServiceTemplate
    template_name = "catalog/template_detail.html"
    context_object_name = "template"

    def get_object(self, queryset=None):
        try:
            return CatalogService.get_template(self.kwargs["pk"])
        except NotFoundError:
            raise Http404
```

`mpp/apps/catalog/urls.py`:
```python
"""Catalog URL patterns."""
from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.TemplateListView.as_view(), name="list"),
    path("<int:pk>/", views.TemplateDetailView.as_view(), name="detail"),
]
```

- [ ] **Step 4: Create templates**

`mpp/templates/catalog/template_list.html`:
```html
{% extends "base.html" %}
{% block title %}Service-Katalog{% endblock %}
{% block content %}
<h1 class="text-2xl font-bold mb-6">Service-Katalog</h1>

<div class="flex gap-4 mb-6">
  <input type="search" name="q" value="{{ request.GET.q|default:'' }}"
         class="input input-bordered flex-1"
         placeholder="Service suchen..."
         hx-get="{% url 'catalog:list' %}"
         hx-target="#template-grid"
         hx-trigger="input changed delay:300ms"
         hx-include="[name='category']">

  <select name="category" class="select select-bordered"
          hx-get="{% url 'catalog:list' %}"
          hx-target="#template-grid"
          hx-trigger="change"
          hx-include="[name='q']">
    <option value="">Alle Kategorien</option>
    {% for value, label in filter_form.fields.category.choices %}
      {% if value %}
        <option value="{{ value }}" {% if request.GET.category == value %}selected{% endif %}>{{ label }}</option>
      {% endif %}
    {% endfor %}
  </select>
</div>

<div id="template-grid">
  {% include "catalog/partials/template_grid.html" %}
</div>
{% endblock %}
```

`mpp/templates/catalog/partials/template_grid.html`:
```html
{% if templates %}
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {% for t in templates %}
  <div class="card bg-base-100 shadow-md hover:shadow-lg transition-shadow">
    <div class="card-body">
      <h2 class="card-title">
        {{ t.name }}
        <span class="badge badge-outline">{{ t.category }}</span>
      </h2>
      <p class="text-sm text-base-content/70">{{ t.description|truncatewords:20 }}</p>
      <div class="text-xs text-base-content/50">
        {{ t.parameters|length }} Parameter · v{{ t.version }}
      </div>
      <div class="card-actions justify-end mt-2">
        <a href="{% url 'catalog:detail' pk=t.pk %}" class="btn btn-primary btn-sm">Details</a>
      </div>
    </div>
  </div>
  {% endfor %}
</div>
{% else %}
<div class="text-center py-12 text-base-content/50">
  Keine Templates gefunden.
</div>
{% endif %}
```

`mpp/templates/catalog/template_detail.html`:
```html
{% extends "base.html" %}
{% block title %}{{ template.name }}{% endblock %}
{% block content %}
<div class="breadcrumbs text-sm mb-4">
  <ul>
    <li><a href="{% url 'catalog:list' %}">Katalog</a></li>
    <li>{{ template.name }}</li>
  </ul>
</div>

<div class="card bg-base-100 shadow-xl">
  <div class="card-body">
    <h1 class="card-title text-2xl">
      {{ template.name }}
      <span class="badge badge-primary">{{ template.category }}</span>
      <span class="badge badge-ghost">v{{ template.version }}</span>
    </h1>
    <p class="mt-2">{{ template.description }}</p>

    {% if template.parameters %}
    <h2 class="text-lg font-semibold mt-6 mb-2">Parameter</h2>
    <div class="overflow-x-auto">
      <table class="table table-zebra">
        <thead>
          <tr>
            <th>Name</th>
            <th>Typ</th>
            <th>Pflicht</th>
            <th>Standard</th>
            <th>Optionen</th>
          </tr>
        </thead>
        <tbody>
          {% for p in template.parameters %}
          <tr>
            <td>{{ p.label|default:p.key }}</td>
            <td><span class="badge badge-sm">{{ p.type }}</span></td>
            <td>{% if p.required %}Ja{% else %}Nein{% endif %}</td>
            <td>{{ p.default|default:"—" }}</td>
            <td>{{ p.options|default_if_none:"—"|join:", " }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    {% endif %}

    <div class="card-actions justify-end mt-6">
      <a href="{% url 'catalog:list' %}" class="btn btn-ghost">Zurück</a>
      <a href="#" class="btn btn-primary">Bestellen</a>
    </div>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 5: Register catalog URLs**

Add to `mpp/config/urls.py`:
```python
path("catalog/", include("apps.catalog.urls")),
```

- [ ] **Step 6: Run tests — verify they pass**

Run: `python -m pytest tests/integration/test_catalog_views.py -v`
Expected: 10 passed.

- [ ] **Step 7: Run ALL tests**

Run: `python -m pytest tests/ -v`
Expected: ~80 passed.

- [ ] **Step 8: Commit**

```bash
git add mpp/apps/catalog/views.py mpp/apps/catalog/forms.py mpp/apps/catalog/urls.py
git add mpp/templates/catalog/ mpp/config/urls.py
git add tests/integration/test_catalog_views.py
git commit -m "feat(B2): add catalog views with HTMX search/filter and DaisyUI templates"
```

---

## Task 5: Seed Command Update & Phase Verification

**Files:**
- Modify: `mpp/apps/accounts/management/commands/seed_users.py` → rename to `seed.py` (or create new `seed.py`)
- Test: run all tests

- [ ] **Step 1: Create unified seed command**

Create `mpp/apps/accounts/management/commands/seed.py`:
```python
"""Management command to seed all demo data."""
from django.core.management.base import BaseCommand
from apps.accounts.services import AccountService
from apps.catalog.services import CatalogService


class Command(BaseCommand):
    help = "Seed demo data (users + catalog templates)"

    def handle(self, *args, **options):
        users = AccountService.seed_stub_users()
        templates = CatalogService.seed_templates()
        self.stdout.write(self.style.SUCCESS(
            f"Seeded {users} user(s) and {templates} template(s)."
        ))
```

- [ ] **Step 2: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: All pass (~80 tests).

- [ ] **Step 3: Run Django check**

Run: `cd mpp && python manage.py check`
Expected: "System check identified no issues."

- [ ] **Step 4: Commit**

```bash
git add mpp/apps/accounts/management/commands/seed.py
git commit -m "feat(B2): add unified seed command for users + catalog templates"
```

---

## Summary

| Task | Description | Tests |
|------|-------------|-------|
| 1 | ServiceTemplate model + admin | 6 |
| 2 | TemplateValidator (domain) | 12 |
| 3 | CatalogService | 13 |
| 4 | Catalog views + templates | 10 |
| 5 | Seed command + verification | 0 |
| **Total new** | | **~41** |
| **Running total** | | **~86** |
