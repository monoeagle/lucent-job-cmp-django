from django.contrib import admin

from .models import GroupSubscription, Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "order_item", "status", "valid_from", "valid_until")
    list_filter = ("status",)
    search_fields = ("user__username",)


@admin.register(GroupSubscription)
class GroupSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "order_item_group", "status")
    list_filter = ("status",)
    search_fields = ("user__username",)
