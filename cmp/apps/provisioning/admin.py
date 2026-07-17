from django.contrib import admin

from .models import DispatchLog


@admin.register(DispatchLog)
class DispatchLogAdmin(admin.ModelAdmin):
    list_display = ["pipeline_id", "order_item", "status", "dispatched_at", "completed_at"]
    list_filter = ["status"]
    readonly_fields = ["dispatched_at", "completed_at"]
