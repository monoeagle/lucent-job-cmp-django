"""Service layer for the catalog app."""
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
            {
                "key": "os_version", "type": "choice", "label": "OS Version",
                "required": True, "default": "ubuntu-24.04",
                "options": ["ubuntu-22.04", "ubuntu-24.04", "debian-12", "rhel-9"],
            },
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
            {
                "key": "os_version", "type": "choice", "label": "OS Version",
                "required": True, "default": "win-server-2025",
                "options": ["win-server-2022", "win-server-2025"],
            },
        ],
    },
    {
        "name": "PostgreSQL DB",
        "category": "database",
        "description": "Managed PostgreSQL Datenbank.",
        "parameters": [
            {
                "key": "version", "type": "choice", "label": "Version",
                "required": True, "default": "16",
                "options": ["14", "15", "16", "17"],
            },
            {"key": "storage_gb", "type": "integer", "label": "Storage (GB)", "required": True, "default": 20},
            {"key": "ha", "type": "boolean", "label": "High Availability", "required": False, "default": False},
        ],
    },
]


class CatalogService:
    """Application service for catalog operations."""

    @staticmethod
    def list_active_templates(category=None):
        """Return active templates, optionally filtered by category."""
        qs = ServiceTemplate.objects.filter(is_active=True)
        if category:
            qs = qs.filter(category=category)
        return list(qs)

    @staticmethod
    def search_templates(query):
        """Search active templates by name or description (case-insensitive)."""
        return list(
            ServiceTemplate.objects.filter(
                Q(is_active=True)
                & (Q(name__icontains=query) | Q(description__icontains=query))
            )
        )

    @staticmethod
    def get_template(template_id):
        """Get a template by ID or raise NotFoundError."""
        try:
            return ServiceTemplate.objects.get(pk=template_id)
        except ServiceTemplate.DoesNotExist:
            raise NotFoundError(
                f"ServiceTemplate with id={template_id} not found."
            )

    @staticmethod
    def validate_template_parameters(template_id, values):
        """Validate parameter values against a template's schema."""
        template = CatalogService.get_template(template_id)
        return TemplateValidator.validate_parameters(template.parameters, values)

    @staticmethod
    def seed_templates():
        """Create seed templates if they don't exist. Returns count created."""
        created = 0
        for data in SEED_TEMPLATES:
            _, was_created = ServiceTemplate.objects.get_or_create(
                name=data["name"], defaults=data,
            )
            if was_created:
                created += 1
        return created
