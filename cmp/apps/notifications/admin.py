from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "is_read", "category", "created_at")
    list_filter = ("is_read", "category")
    search_fields = ("title", "message")
