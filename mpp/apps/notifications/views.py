from django.contrib import messages
from django.shortcuts import redirect
from django.views import View
from django.views.generic import ListView

from core.mixins import RequesterRequiredMixin

from .services import NotificationService


class NotificationListView(RequesterRequiredMixin, ListView):
    template_name = "notifications/notification_list.html"
    context_object_name = "notifications"

    def get_queryset(self):
        return NotificationService.list_all(self.request.user.pk)


class NotificationMarkReadView(RequesterRequiredMixin, View):
    def post(self, request, pk):
        NotificationService.mark_read(pk)
        return redirect("notifications:list")


class NotificationMarkAllReadView(RequesterRequiredMixin, View):
    def post(self, request):
        NotificationService.mark_all_read(request.user.pk)
        messages.success(request, "Alle als gelesen markiert.")
        return redirect("notifications:list")
