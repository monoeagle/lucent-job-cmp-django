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
            template=t,
            parameter_key="os_version",
            context_field="location",
            allowed_values=["ubuntu-22.04"],
        )
        assert r.pk is not None

    def test_str(self):
        t = ServiceTemplateFactory(name="Linux VM")
        r = ContextRestriction.objects.create(
            template=t,
            parameter_key="os_version",
            context_field="location",
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
