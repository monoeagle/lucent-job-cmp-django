"""Order views for list, detail, create, submit, add-item, remove-item."""
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
    """Display list of orders with workspace tabs and status filtering."""

    template_name = "orders/order_list.html"
    context_object_name = "orders"

    def _can_see_all(self):
        """Return True if the user may view all orders (approver+)."""
        from apps.accounts.services import AccountService
        from core.domain.enums import UserRole

        return AccountService.is_at_least_role(
            self.request.user.role, UserRole.APPROVER
        )

    def get_queryset(self):
        tab = self.request.GET.get("tab", "mine")
        if tab == "all" and self._can_see_all():
            qs = Order.objects.select_related("user").all()
        else:
            qs = Order.objects.filter(user=self.request.user).select_related(
                "user"
            )
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_tab"] = self.request.GET.get("tab", "mine")
        ctx["current_status"] = self.request.GET.get("status", "")
        ctx["can_see_all"] = self._can_see_all()
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
        # For the "Add Service" dropdown in draft orders
        if self.object.status == "draft":
            ctx["templates"] = CatalogService.list_active_templates()
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


class OrderAddItemView(RequesterRequiredMixin, FormView):
    """Add an item to an existing draft order."""

    template_name = "orders/order_add_item.html"

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
        ctx["order_pk"] = self.kwargs["pk"]
        return ctx

    def form_valid(self, form):
        template = self.get_template_obj()
        params = {
            p["key"]: form.cleaned_data[p["key"]]
            for p in template.parameters
            if p["key"] in form.cleaned_data
        }
        try:
            OrderService.add_item(
                order_id=self.kwargs["pk"],
                template_id=template.pk,
                parameters=params,
            )
            messages.success(self.request, f"{template.name} hinzugefügt.")
            return redirect("orders:detail", pk=self.kwargs["pk"])
        except (ValidationError, ConflictError) as e:
            messages.error(self.request, e.message)
            return self.form_invalid(form)


class OrderRemoveItemView(RequesterRequiredMixin, View):
    """Remove an item from a draft order."""

    def post(self, request, pk, item_pk):
        try:
            OrderService.remove_item(item_id=item_pk)
            messages.success(request, "Position entfernt.")
        except (NotFoundError, ConflictError) as e:
            messages.error(request, e.message)
        return redirect("orders:detail", pk=pk)


class OrderSubmitView(RequesterRequiredMixin, View):
    """Submit a draft order for processing."""

    def post(self, request, pk):
        try:
            OrderService.submit_order(order_id=pk)
            messages.success(request, "Bestellung eingereicht.")
        except (ValidationError, ConflictError) as e:
            messages.error(request, e.message)
        return redirect("orders:detail", pk=pk)
