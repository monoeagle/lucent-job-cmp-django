from django.contrib.auth.models import AbstractUser
from django.db import models
from core.domain.enums import UserRole
from core.mixins import TimeStampedModel


class User(TimeStampedModel, AbstractUser):
    """Custom user with role field."""
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.REQUESTER,
    )

    class Meta:
        db_table = "users"
        ordering = ["username"]

    def __str__(self):
        return self.username
