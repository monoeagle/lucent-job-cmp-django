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
        AvailabilityRule.objects.create(
            template=t, location="loc-fra", is_available=True,
        )
        assert ContextService.is_template_available(t.pk, location="loc-fra") is True

    def test_template_unavailable_with_blocking_rule(self):
        t = ServiceTemplateFactory()
        AvailabilityRule.objects.create(
            template=t, location="loc-fra", is_available=False,
        )
        assert ContextService.is_template_available(t.pk, location="loc-fra") is False

    def test_available_templates_for_context(self):
        t1 = ServiceTemplateFactory(name="Available")
        t2 = ServiceTemplateFactory(name="Blocked")
        AvailabilityRule.objects.create(
            template=t2, location="loc-fra", is_available=False,
        )
        available = ContextService.get_available_templates(location="loc-fra")
        names = [t.name for t in available]
        assert "Available" in names
        assert "Blocked" not in names


@pytest.mark.django_db
class TestContextServiceRestrictions:
    def test_no_restrictions_returns_empty(self):
        t = ServiceTemplateFactory()
        assert ContextService.get_parameter_restrictions(t.pk, "location", "loc-fra") == {}

    def test_restriction_limits_values(self):
        t = ServiceTemplateFactory()
        ContextRestriction.objects.create(
            template=t,
            parameter_key="os_version",
            context_field="location",
            allowed_values=["ubuntu-22.04"],
        )
        r = ContextService.get_parameter_restrictions(t.pk, "location", "loc-fra")
        assert r == {"os_version": ["ubuntu-22.04"]}


@pytest.mark.django_db
class TestContextServiceTenants:
    def test_user_tenants(self):
        user = UserFactory()
        UserTenantAssignment.objects.create(user=user, tenant="tenant-alpha")
        UserTenantAssignment.objects.create(user=user, tenant="tenant-beta")
        tenants = ContextService.get_user_tenants(user.pk)
        assert len(tenants) == 2

    def test_user_without_tenants(self):
        user = UserFactory()
        assert ContextService.get_user_tenants(user.pk) == []
