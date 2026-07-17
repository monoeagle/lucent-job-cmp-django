"""Domain enums — no Django dependencies except TextChoices."""
from django.db import models


class UserRole(models.TextChoices):
    REQUESTER = "requester", "Requester"
    APPROVER = "approver", "Approver"
    ADMIN = "admin", "Admin"
    SUPERADMIN = "superadmin", "Superadmin"
