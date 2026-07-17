from django.contrib import admin

from .models import ApprovalRequest, ApprovalRule


@admin.register(ApprovalRule)
class ApprovalRuleAdmin(admin.ModelAdmin):
    list_display = ["template", "approver_role", "is_active"]
    list_filter = ["is_active", "approver_role"]


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ["pk", "order", "status", "decided_by", "created_at"]
    list_filter = ["status"]
