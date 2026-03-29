"""Test CatalogService."""
import pytest
from apps.catalog.services import CatalogService
from apps.catalog.models import ServiceTemplate
from core.exceptions import NotFoundError
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
        assert len(CatalogService.list_active_templates()) == 0

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
        assert CatalogService.get_template(t.pk).name == "Test"

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
    def test_seed_creates_templates(self):
        assert CatalogService.seed_templates() == 2
        assert ServiceTemplate.objects.count() == 2

    def test_seed_is_idempotent(self):
        CatalogService.seed_templates()
        assert CatalogService.seed_templates() == 0
