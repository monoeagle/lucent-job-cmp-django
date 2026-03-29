"""Notification views."""
from django.contrib import messages
from django.shortcuts import redirect
from django.views import View
from django.views.generic import ListView
from core.mixins import RequesterRequiredMixin
from .models import Notification
from .services import NotificationService


class NotificationListView(RequesterRequiredMixin, ListView):
    template_name = "notifications/notification_list.html"
    context_object_name = "notifications"

    def get_queryset(self):
        tab = self.request.GET.get("tab", "all")
        qs = Notification.objects.filter(user=self.request.user)
        if tab == "unread":
            qs = qs.filter(is_read=False)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_tab"] = self.request.GET.get("tab", "all")
        ctx["unread_count"] = NotificationService.unread_count(
            self.request.user.pk
        )
        return ctx


class NotificationMarkReadView(RequesterRequiredMixin, View):
    def post(self, request, pk):
        NotificationService.mark_read(pk)
        return redirect("notifications:list")


class NotificationMarkAllReadView(RequesterRequiredMixin, View):
    def post(self, request):
        NotificationService.mark_all_read(request.user.pk)
        messages.success(request, "Alle als gelesen markiert.")
        return redirect("notifications:list")
