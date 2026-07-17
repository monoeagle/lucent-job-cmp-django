from django.db import models

from core.mixins import TimeStampedModel


class TemplateCategory(models.TextChoices):
    COMPUTE = "compute", "Compute"
    DATABASE = "database", "Database"
    CONTAINER = "container", "Container"
    NETWORK = "network", "Network"
    STORAGE = "storage", "Storage"


class ServiceTemplate(TimeStampedModel):
    name = models.CharField(max_length=200, unique=True)
    category = models.CharField(max_length=30)
    description = models.TextField(blank=True, default="")
    parameters = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "service_templates"
        ordering = ["name"]

    def __str__(self):
        return self.name
