from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "action", "resource_type", "resource_id")
    list_filter = ("action", "resource_type")
    search_fields = ("action", "resource_type")
    readonly_fields = ("timestamp",)
