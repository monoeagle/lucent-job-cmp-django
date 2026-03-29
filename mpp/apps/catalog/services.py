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
            {"key": "cpu", "type": "integer", "label": "CPUs", "required": True, "default": 2,
             "group": "sizing", "display_order": 1},
            {"key": "ram_gb", "type": "integer", "label": "RAM (GB)", "required": True, "default": 4,
             "group": "sizing", "display_order": 2},
            {"key": "disk_gb", "type": "integer", "label": "Disk (GB)", "required": True, "default": 50,
             "group": "sizing", "display_order": 3},
            {"key": "os_version", "type": "choice", "label": "OS Version", "required": True,
             "options": ["ubuntu-22.04", "ubuntu-24.04", "debian-12", "rhel-9", "almalinux-10"],
             "default": "ubuntu-24.04", "group": "os", "display_order": 4},
            {"key": "hostname", "type": "string", "label": "Hostname", "required": True,
             "group": "server", "display_order": 5},
            {"key": "ha", "type": "boolean", "label": "High Availability", "required": False, "default": False,
             "group": "server", "display_order": 6},
            {"key": "backup", "type": "choice", "label": "Backup", "required": True,
             "options": ["none", "daily", "weekly"], "default": "daily",
             "group": "backup", "display_order": 7},
            {"key": "extra_disk_gb", "type": "integer", "label": "Extra Disk (GB)", "required": False, "default": 0,
             "group": "sizing", "display_order": 8},
        ],
    },
    {
        "name": "Windows VM",
        "category": "compute",
        "description": "Windows Server Virtual Machine.",
        "parameters": [
            {"key": "cpu", "type": "integer", "label": "CPUs", "required": True, "default": 4,
             "group": "sizing", "display_order": 1},
            {"key": "ram_gb", "type": "integer", "label": "RAM (GB)", "required": True, "default": 8,
             "group": "sizing", "display_order": 2},
            {"key": "disk_gb", "type": "integer", "label": "Disk (GB)", "required": True, "default": 100,
             "group": "sizing", "display_order": 3},
            {"key": "os_version", "type": "choice", "label": "OS Version", "required": True,
             "options": ["win-server-2019", "win-server-2022", "win-server-2025"],
             "default": "win-server-2025", "group": "os", "display_order": 4},
            {"key": "hostname", "type": "string", "label": "Hostname", "required": True,
             "group": "server", "display_order": 5},
            {"key": "domain_join", "type": "boolean", "label": "Domain Join", "required": False, "default": True,
             "group": "server", "display_order": 6},
            {"key": "backup", "type": "choice", "label": "Backup", "required": True,
             "options": ["none", "daily", "weekly"], "default": "daily",
             "group": "backup", "display_order": 7},
            {"key": "extra_disk_gb", "type": "integer", "label": "Extra Disk (GB)", "required": False, "default": 0,
             "group": "sizing", "display_order": 8},
        ],
    },
    {
        "name": "PostgreSQL DB",
        "category": "database",
        "description": "Managed PostgreSQL Datenbank.",
        "parameters": [
            {"key": "version", "type": "choice", "label": "Version", "required": True,
             "options": ["14", "15", "16", "17"], "default": "16",
             "group": "database", "display_order": 1},
            {"key": "storage_gb", "type": "integer", "label": "Storage (GB)", "required": True, "default": 20,
             "group": "database", "display_order": 2},
            {"key": "ha", "type": "boolean", "label": "High Availability", "required": False, "default": False,
             "group": "database", "display_order": 3},
            {"key": "backup", "type": "choice", "label": "Backup", "required": True,
             "options": ["none", "daily", "weekly", "continuous"], "default": "daily",
             "group": "backup", "display_order": 4},
            {"key": "db_name", "type": "string", "label": "Datenbankname", "required": True,
             "group": "database", "display_order": 5},
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
