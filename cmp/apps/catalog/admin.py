from django.contrib import admin

from .models import ServiceTemplate


@admin.register(ServiceTemplate)
class ServiceTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "is_active", "version", "created_at"]
    list_filter = ["category", "is_active"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]
