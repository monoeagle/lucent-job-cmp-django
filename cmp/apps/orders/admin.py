"""Admin configuration for orders."""
from django.contrib import admin

from .models import Order, OrderItem, OrderItemGroup


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["pk", "user", "status", "created_at"]
    list_filter = ["status"]
    inlines = [OrderItemInline]


@admin.register(OrderItemGroup)
class OrderItemGroupAdmin(admin.ModelAdmin):
    list_display = ["pk", "order", "template", "quantity"]
