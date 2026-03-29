# Phase B4: Context & CMDB — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the CMDB stub system — YAML-based location/network/tenant data, availability rules for service templates, and context-dependent parameter restrictions.

**Architecture:** `apps/cmdb/` with models (AvailabilityRule, ContextRestriction, UserTenantAssignment), a YAML-based CmdbStubClient, and a ContextService. Stub data in `mpp/stubs/cmdb/`.

**Tech Stack:** Django 6.0, PostgreSQL, PyYAML, pytest-django, factory_boy

---

## File Structure

```
mpp/stubs/
└── cmdb/
    ├── locations.yml
    ├── networks.yml
    └── tenants.yml

mpp/apps/cmdb/
├── __init__.py
├── apps.py
├── models.py              # AvailabilityRule, ContextRestriction, UserTenantAssignment
├── services.py            # ContextService
├── clients.py             # CmdbStubClient
├── admin.py
└── urls.py

mpp/templates/cmdb/
└── context_info.html      # Optional: show available contexts

tests/
├── unit/
│   ├── test_cmdb_client.py
│   └── test_context_service.py
└── integration/
    └── test_cmdb_model.py
```

---

## Task 1: CMDB Stub Data & Client

**Files:**
- Create: `mpp/stubs/cmdb/locations.yml`
- Create: `mpp/stubs/cmdb/networks.yml`
- Create: `mpp/stubs/cmdb/tenants.yml`
- Create: `mpp/apps/cmdb/__init__.py`, `apps.py`, `clients.py`
- Test: `tests/unit/test_cmdb_client.py`

**Stub YAML Data:**

`mpp/stubs/cmdb/locations.yml`:
```yaml
- id: loc-fra
  name: Frankfurt
  datacenter: DC-FRA-01
- id: loc-ber
  name: Berlin
  datacenter: DC-BER-01
- id: loc-muc
  name: München
  datacenter: DC-MUC-01
```

`mpp/stubs/cmdb/networks.yml`:
```yaml
- id: net-prod-fra
  name: Production Frankfurt
  location_id: loc-fra
  vlan: 100
  cidr: "10.1.0.0/24"
  zone: production
- id: net-dev-fra
  name: Development Frankfurt
  location_id: loc-fra
  vlan: 200
  cidr: "10.2.0.0/24"
  zone: development
- id: net-prod-ber
  name: Production Berlin
  location_id: loc-ber
  vlan: 100
  cidr: "10.3.0.0/24"
  zone: production
- id: net-mgmt-fra
  name: Management Frankfurt
  location_id: loc-fra
  vlan: 300
  cidr: "10.4.0.0/24"
  zone: management
- id: net-dev-ber
  name: Development Berlin
  location_id: loc-ber
  vlan: 200
  cidr: "10.5.0.0/24"
  zone: development
- id: net-prod-muc
  name: Production München
  location_id: loc-muc
  vlan: 100
  cidr: "10.6.0.0/24"
  zone: production
- id: net-dev-muc
  name: Development München
  location_id: loc-muc
  vlan: 200
  cidr: "10.7.0.0/24"
  zone: development
```

`mpp/stubs/cmdb/tenants.yml`:
```yaml
- id: tenant-alpha
  name: Alpha Corp
- id: tenant-beta
  name: Beta GmbH
```

**Tests** `tests/unit/test_cmdb_client.py`:
```python
"""Test CMDB stub client."""
from apps.cmdb.clients import CmdbStubClient

class TestCmdbStubClient:
    def setup_method(self):
        self.client = CmdbStubClient()

    def test_list_locations(self):
        locations = self.client.list_locations()
        assert len(locations) == 3
        assert locations[0]["id"] == "loc-fra"

    def test_list_networks(self):
        networks = self.client.list_networks()
        assert len(networks) == 7

    def test_list_networks_by_location(self):
        networks = self.client.list_networks(location_id="loc-fra")
        assert len(networks) == 3
        assert all(n["location_id"] == "loc-fra" for n in networks)

    def test_list_networks_by_zone(self):
        networks = self.client.list_networks(zone="production")
        assert len(networks) == 3

    def test_list_tenants(self):
        tenants = self.client.list_tenants()
        assert len(tenants) == 2

    def test_get_location_by_id(self):
        loc = self.client.get_location("loc-fra")
        assert loc["name"] == "Frankfurt"

    def test_get_location_not_found(self):
        loc = self.client.get_location("nonexistent")
        assert loc is None

    def test_get_zones(self):
        zones = self.client.get_zones()
        assert "production" in zones
        assert "development" in zones
        assert "management" in zones
```

**Implementation** `mpp/apps/cmdb/clients.py`:
```python
"""CMDB stub client — reads from YAML files."""
from pathlib import Path
import yaml

STUBS_DIR = Path(__file__).resolve().parent.parent.parent / "stubs" / "cmdb"


class CmdbStubClient:
    def __init__(self):
        self._locations = self._load("locations.yml")
        self._networks = self._load("networks.yml")
        self._tenants = self._load("tenants.yml")

    def _load(self, filename):
        path = STUBS_DIR / filename
        with open(path) as f:
            return yaml.safe_load(f)

    def list_locations(self):
        return self._locations

    def list_networks(self, location_id=None, zone=None):
        nets = self._networks
        if location_id:
            nets = [n for n in nets if n["location_id"] == location_id]
        if zone:
            nets = [n for n in nets if n["zone"] == zone]
        return nets

    def list_tenants(self):
        return self._tenants

    def get_location(self, location_id):
        for loc in self._locations:
            if loc["id"] == location_id:
                return loc
        return None

    def get_zones(self):
        return sorted(set(n["zone"] for n in self._networks))
```

Commit: `git commit -m "feat(B4): add CMDB stub client with YAML data"`

---

## Task 2: CMDB Models (AvailabilityRule, ContextRestriction, UserTenantAssignment)

**Files:**
- Create: `mpp/apps/cmdb/models.py`, `admin.py`
- Modify: `mpp/config/settings/base.py` (add apps.cmdb)
- Test: `tests/integration/test_cmdb_model.py`

**Tests** `tests/integration/test_cmdb_model.py`:
```python
"""Test CMDB models."""
import pytest
from apps.cmdb.models import AvailabilityRule, ContextRestriction, UserTenantAssignment
from tests.factories import UserFactory, ServiceTemplateFactory


@pytest.mark.django_db
class TestAvailabilityRule:
    def test_create_rule(self):
        t = ServiceTemplateFactory()
        rule = AvailabilityRule.objects.create(
            template=t, location="loc-fra", tenant="tenant-alpha", is_available=True,
        )
        assert rule.pk is not None

    def test_str(self):
        t = ServiceTemplateFactory(name="Linux VM")
        rule = AvailabilityRule.objects.create(
            template=t, location="loc-fra", tenant="tenant-alpha",
        )
        assert "Linux VM" in str(rule)

    def test_default_is_available(self):
        t = ServiceTemplateFactory()
        rule = AvailabilityRule.objects.create(template=t, location="loc-fra")
        assert rule.is_available is True


@pytest.mark.django_db
class TestContextRestriction:
    def test_create_restriction(self):
        t = ServiceTemplateFactory()
        r = ContextRestriction.objects.create(
            template=t, parameter_key="os_version",
            context_field="location",
            allowed_values=["ubuntu-22.04", "ubuntu-24.04"],
        )
        assert r.pk is not None

    def test_str(self):
        t = ServiceTemplateFactory(name="Linux VM")
        r = ContextRestriction.objects.create(
            template=t, parameter_key="os_version", context_field="location",
            allowed_values=["ubuntu-22.04"],
        )
        assert "os_version" in str(r)


@pytest.mark.django_db
class TestUserTenantAssignment:
    def test_create_assignment(self):
        user = UserFactory()
        a = UserTenantAssignment.objects.create(user=user, tenant="tenant-alpha")
        assert a.pk is not None

    def test_user_can_have_multiple_tenants(self):
        user = UserFactory()
        UserTenantAssignment.objects.create(user=user, tenant="tenant-alpha")
        UserTenantAssignment.objects.create(user=user, tenant="tenant-beta")
        assert UserTenantAssignment.objects.filter(user=user).count() == 2
```

**Implementation** `mpp/apps/cmdb/models.py`:
```python
from django.conf import settings
from django.db import models
from core.mixins import TimeStampedModel


class AvailabilityRule(TimeStampedModel):
    template = models.ForeignKey("catalog.ServiceTemplate", on_delete=models.CASCADE, related_name="availability_rules")
    location = models.CharField(max_length=50, blank=True, default="")
    tenant = models.CharField(max_length=50, blank=True, default="")
    is_available = models.BooleanField(default=True)

    class Meta:
        db_table = "availability_rules"

    def __str__(self):
        return f"{self.template.name} @ {self.location or '*'}/{self.tenant or '*'}"


class ContextRestriction(TimeStampedModel):
    template = models.ForeignKey("catalog.ServiceTemplate", on_delete=models.CASCADE, related_name="context_restrictions")
    parameter_key = models.CharField(max_length=50)
    context_field = models.CharField(max_length=50)
    allowed_values = models.JSONField(default=list)

    class Meta:
        db_table = "context_restrictions"

    def __str__(self):
        return f"{self.template.name}: {self.parameter_key} restricted by {self.context_field}"


class UserTenantAssignment(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tenant_assignments")
    tenant = models.CharField(max_length=50)

    class Meta:
        db_table = "user_tenant_assignments"
        unique_together = [("user", "tenant")]

    def __str__(self):
        return f"{self.user.username} → {self.tenant}"
```

Commit: `git commit -m "feat(B4): add AvailabilityRule, ContextRestriction, UserTenantAssignment models"`

---

## Task 3: ContextService

**Files:**
- Create: `mpp/apps/cmdb/services.py`
- Test: `tests/unit/test_context_service.py`

**Tests** `tests/unit/test_context_service.py`:
```python
"""Test ContextService."""
import pytest
from apps.cmdb.models import AvailabilityRule, ContextRestriction, UserTenantAssignment
from apps.cmdb.services import ContextService
from tests.factories import UserFactory, ServiceTemplateFactory


@pytest.mark.django_db
class TestContextServiceAvailability:
    def test_template_available_when_no_rules(self):
        t = ServiceTemplateFactory()
        assert ContextService.is_template_available(t.pk, location="loc-fra") is True

    def test_template_available_with_matching_rule(self):
        t = ServiceTemplateFactory()
        AvailabilityRule.objects.create(template=t, location="loc-fra", is_available=True)
        assert ContextService.is_template_available(t.pk, location="loc-fra") is True

    def test_template_unavailable_with_blocking_rule(self):
        t = ServiceTemplateFactory()
        AvailabilityRule.objects.create(template=t, location="loc-fra", is_available=False)
        assert ContextService.is_template_available(t.pk, location="loc-fra") is False

    def test_available_templates_for_context(self):
        t1 = ServiceTemplateFactory(name="Available")
        t2 = ServiceTemplateFactory(name="Blocked")
        AvailabilityRule.objects.create(template=t2, location="loc-fra", is_available=False)
        available = ContextService.get_available_templates(location="loc-fra")
        names = [t.name for t in available]
        assert "Available" in names
        assert "Blocked" not in names


@pytest.mark.django_db
class TestContextServiceRestrictions:
    def test_no_restrictions_returns_empty(self):
        t = ServiceTemplateFactory()
        restrictions = ContextService.get_parameter_restrictions(t.pk, context_field="location", context_value="loc-fra")
        assert restrictions == {}

    def test_restriction_limits_values(self):
        t = ServiceTemplateFactory()
        ContextRestriction.objects.create(
            template=t, parameter_key="os_version",
            context_field="location", allowed_values=["ubuntu-22.04"],
        )
        restrictions = ContextService.get_parameter_restrictions(t.pk, context_field="location", context_value="loc-fra")
        assert restrictions == {"os_version": ["ubuntu-22.04"]}


@pytest.mark.django_db
class TestContextServiceTenants:
    def test_user_tenants(self):
        user = UserFactory()
        UserTenantAssignment.objects.create(user=user, tenant="tenant-alpha")
        UserTenantAssignment.objects.create(user=user, tenant="tenant-beta")
        tenants = ContextService.get_user_tenants(user.pk)
        assert len(tenants) == 2
        assert "tenant-alpha" in tenants

    def test_user_without_tenants(self):
        user = UserFactory()
        tenants = ContextService.get_user_tenants(user.pk)
        assert tenants == []
```

**Implementation** `mpp/apps/cmdb/services.py`:
```python
from apps.catalog.models import ServiceTemplate
from apps.cmdb.models import AvailabilityRule, ContextRestriction, UserTenantAssignment


class ContextService:
    @staticmethod
    def is_template_available(template_id, location="", tenant=""):
        rules = AvailabilityRule.objects.filter(template_id=template_id)
        if location:
            location_rules = rules.filter(location=location)
            if location_rules.exists():
                if location_rules.filter(is_available=False).exists():
                    return False
        if tenant:
            tenant_rules = rules.filter(tenant=tenant)
            if tenant_rules.exists():
                if tenant_rules.filter(is_available=False).exists():
                    return False
        return True

    @staticmethod
    def get_available_templates(location="", tenant=""):
        templates = ServiceTemplate.objects.filter(is_active=True)
        blocked_ids = set()
        if location:
            blocked = AvailabilityRule.objects.filter(
                location=location, is_available=False,
            ).values_list("template_id", flat=True)
            blocked_ids.update(blocked)
        if tenant:
            blocked = AvailabilityRule.objects.filter(
                tenant=tenant, is_available=False,
            ).values_list("template_id", flat=True)
            blocked_ids.update(blocked)
        if blocked_ids:
            templates = templates.exclude(pk__in=blocked_ids)
        return list(templates)

    @staticmethod
    def get_parameter_restrictions(template_id, context_field, context_value):
        restrictions = ContextRestriction.objects.filter(
            template_id=template_id, context_field=context_field,
        )
        result = {}
        for r in restrictions:
            result[r.parameter_key] = r.allowed_values
        return result

    @staticmethod
    def get_user_tenants(user_id):
        return list(
            UserTenantAssignment.objects.filter(user_id=user_id)
            .values_list("tenant", flat=True)
        )
```

Commit: `git commit -m "feat(B4): add ContextService with availability, restrictions, tenants"`

---

## Summary

| Task | Description | Tests |
|------|-------------|-------|
| 1 | CMDB Stub Client + YAML data | 8 |
| 2 | CMDB Models (3 models) | 7 |
| 3 | ContextService | 8 |
| **Total new** | | **~23** |
| **Running total** | | **~162** |
