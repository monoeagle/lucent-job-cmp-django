"""Views for the subscriptions app."""
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.views import View
from django.views.generic import DetailView, ListView

from core.exceptions import ConflictError, NotFoundError
from core.mixins import RequesterRequiredMixin

from .services import SubscriptionService


class SubscriptionListView(RequesterRequiredMixin, ListView):
    """List all subscriptions for the current user."""

    template_name = "subscriptions/subscription_list.html"
    context_object_name = "subscriptions"

    def get_queryset(self):
        return SubscriptionService.list_user_subscriptions(
            self.request.user.pk
        )


class SubscriptionDetailView(RequesterRequiredMixin, DetailView):
    """Show details for a single subscription."""

    template_name = "subscriptions/subscription_detail.html"
    context_object_name = "subscription"

    def get_object(self, queryset=None):
        try:
            return SubscriptionService.get_subscription(self.kwargs["pk"])
        except NotFoundError:
            raise Http404


class SubscriptionCancelView(RequesterRequiredMixin, View):
    """Cancel an active subscription."""

    def post(self, request, pk):
        try:
            SubscriptionService.cancel(pk)
            messages.success(request, "Subscription gekuendigt.")
        except (ConflictError, NotFoundError) as e:
            messages.error(request, e.message)
        return redirect("subscriptions:list")
