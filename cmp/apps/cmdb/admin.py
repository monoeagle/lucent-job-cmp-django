from django.contrib import admin

from .models import AvailabilityRule, ContextRestriction, UserTenantAssignment


@admin.register(AvailabilityRule)
class AvailabilityRuleAdmin(admin.ModelAdmin):
    list_display = ["template", "location", "tenant", "is_available"]
    list_filter = ["is_available"]


@admin.register(ContextRestriction)
class ContextRestrictionAdmin(admin.ModelAdmin):
    list_display = ["template", "parameter_key", "context_field"]


@admin.register(UserTenantAssignment)
class UserTenantAssignmentAdmin(admin.ModelAdmin):
    list_display = ["user", "tenant"]
