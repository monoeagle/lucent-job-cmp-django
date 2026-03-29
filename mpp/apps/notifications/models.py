from django.conf import settings
from django.db import models

from core.mixins import TimeStampedModel


class Notification(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    category = models.CharField(max_length=50, blank=True, default="info")

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]

    def __str__(self):
        status = "read" if self.is_read else "unread"
        return f"[{status}] {self.title}"
