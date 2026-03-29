"""Order views for list, detail, create and submit."""
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.views import View
from django.views.generic import ListView, DetailView, FormView

from apps.catalog.services import CatalogService
from core.exceptions import ConflictError, NotFoundError, ValidationError
from core.mixins import RequesterRequiredMixin

from .forms import OrderParameterForm
from .models import Order
from .services import OrderService


class OrderListView(RequesterRequiredMixin, ListView):
    """Display list of orders belonging to the current user."""

    template_name = "orders/order_list.html"
    context_object_name = "orders"

    def get_queryset(self):
        qs = Order.objects.filter(user=self.request.user).select_related("user")
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_status"] = self.request.GET.get("status", "")
        return ctx


class OrderDetailView(RequesterRequiredMixin, DetailView):
    """Display a single order with its items."""

    template_name = "orders/order_detail.html"
    context_object_name = "order"

    def get_object(self, queryset=None):
        try:
            return OrderService.get_order(self.kwargs["pk"])
        except NotFoundError:
            raise Http404

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["items"] = self.object.items.select_related("template").all()
        return ctx


class OrderCreateView(RequesterRequiredMixin, FormView):
    """Create a new order from a service template."""

    template_name = "orders/order_create.html"

    def get_template_obj(self):
        try:
            return CatalogService.get_template(self.kwargs["template_pk"])
        except NotFoundError:
            raise Http404

    def get_form(self, form_class=None):
        template = self.get_template_obj()
        return OrderParameterForm(
            self.request.POST or None,
            template_parameters=template.parameters,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["service_template"] = self.get_template_obj()
        return ctx

    def form_valid(self, form):
        template = self.get_template_obj()
        params = {}
        for param in template.parameters:
            key = param["key"]
            if key in form.cleaned_data:
                params[key] = form.cleaned_data[key]
        try:
            order = OrderService.create_order(user=self.request.user)
            OrderService.add_item(
                order_id=order.pk,
                template_id=template.pk,
                parameters=params,
            )
            messages.success(self.request, f"Bestellung #{order.pk} erstellt.")
            return redirect("orders:detail", pk=order.pk)
        except (ValidationError, ConflictError) as e:
            messages.error(self.request, e.message)
            return self.form_invalid(form)


class OrderSubmitView(RequesterRequiredMixin, View):
    """Submit a draft order for processing."""

    def post(self, request, pk):
        try:
            OrderService.submit_order(order_id=pk)
            messages.success(request, "Bestellung eingereicht.")
        except (ValidationError, ConflictError) as e:
            messages.error(request, e.message)
        return redirect("orders:detail", pk=pk)
