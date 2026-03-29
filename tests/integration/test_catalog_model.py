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
