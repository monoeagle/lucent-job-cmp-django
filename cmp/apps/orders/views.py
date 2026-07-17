"""Order views for list, detail, create (wizard), submit, add-item, remove-item."""
from django import forms
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import ListView, DetailView, FormView

from apps.catalog.services import CatalogService
from core.exceptions import ConflictError, NotFoundError, ValidationError
from core.mixins import RequesterRequiredMixin

from .forms import (
    ContextForm,
    FullOrderForm,
    OrderParameterForm,
    ParameterGroupForm,
    QuantityForm,
)
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
        tab = self.request.GET.get("tab", "all")
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
        ctx["current_tab"] = self.request.GET.get("tab", "all")
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


class OrderCreateView(RequesterRequiredMixin, View):
    """Multi-step order wizard with session state."""

    def _get_template(self, template_pk):
        try:
            return CatalogService.get_template(template_pk)
        except NotFoundError:
            raise Http404

    def _get_steps(self, template):
        """Build wizard steps from template parameters."""
        steps = []

        # Step 0: Context
        steps.append({
            "key": "context",
            "label": "Kontext",
            "type": "context",
        })

        # Group parameters by 'group' field
        groups = {}
        for param in template.parameters:
            group = param.get("group", "Allgemein")
            if group not in groups:
                groups[group] = []
            groups[group].append(param)

        # Sort groups by first param's display_order
        sorted_groups = sorted(
            groups.items(),
            key=lambda g: min(p.get("display_order", 999) for p in g[1]),
        )

        for group_name, params in sorted_groups:
            steps.append({
                "key": f"params_{group_name}",
                "label": group_name.replace("_", " ").title(),
                "type": "params",
                "parameters": params,
            })

        # Final step: Summary
        steps.append({
            "key": "summary",
            "label": "Zusammenfassung",
            "type": "summary",
        })

        return steps

    def _get_session_key(self, template_pk):
        return f"wizard_{template_pk}"

    def _get_wizard_data(self, request, template_pk):
        return request.session.get(self._get_session_key(template_pk), {
            "current_step": 0,
            "context": {},
            "parameters": {},
            "quantity": 1,
        })

    def _save_wizard_data(self, request, template_pk, data):
        request.session[self._get_session_key(template_pk)] = data
        request.session.modified = True

    def _clear_wizard_data(self, request, template_pk):
        key = self._get_session_key(template_pk)
        if key in request.session:
            del request.session[key]

    def get(self, request, template_pk):
        template = self._get_template(template_pk)
        steps = self._get_steps(template)
        wizard_data = self._get_wizard_data(request, template_pk)
        current_step = int(
            request.GET.get("step", wizard_data["current_step"])
        )

        # Clamp step
        current_step = max(0, min(current_step, len(steps) - 1))
        wizard_data["current_step"] = current_step
        self._save_wizard_data(request, template_pk, wizard_data)

        step = steps[current_step]
        form = self._get_form_for_step(step, wizard_data)

        context = self._build_context(
            template, steps, current_step, step, form, wizard_data,
        )
        return render(request, "orders/wizard/wizard.html", context)

    def post(self, request, template_pk):
        template = self._get_template(template_pk)
        steps = self._get_steps(template)
        wizard_data = self._get_wizard_data(request, template_pk)
        current_step = wizard_data["current_step"]
        step = steps[current_step]

        action = request.POST.get("action", "next")

        if action == "back":
            wizard_data["current_step"] = max(0, current_step - 1)
            self._save_wizard_data(request, template_pk, wizard_data)
            return redirect(
                f"{request.path}?step={wizard_data['current_step']}"
            )

        if action == "goto":
            target = int(request.POST.get("target_step", 0))
            if target <= current_step:  # Can only go back
                wizard_data["current_step"] = target
                self._save_wizard_data(request, template_pk, wizard_data)
                return redirect(f"{request.path}?step={target}")
            return redirect(f"{request.path}?step={current_step}")

        # Validate current step
        form = self._get_form_for_step(step, wizard_data, data=request.POST)

        if not form.is_valid():
            context = self._build_context(
                template, steps, current_step, step, form, wizard_data,
            )
            return render(request, "orders/wizard/wizard.html", context)

        # Save step data
        if step["type"] == "context":
            wizard_data["context"] = form.cleaned_data
        elif step["type"] == "params":
            for key, value in form.cleaned_data.items():
                wizard_data["parameters"][key] = value
        elif step["type"] == "summary":
            wizard_data["quantity"] = form.cleaned_data.get("quantity", 1)

        if action == "submit":
            return self._submit_order(
                request, template, wizard_data, template_pk,
            )

        # Move to next step
        wizard_data["current_step"] = min(
            current_step + 1, len(steps) - 1,
        )
        self._save_wizard_data(request, template_pk, wizard_data)
        return redirect(f"{request.path}?step={wizard_data['current_step']}")

    def _build_context(
        self, template, steps, current_step, step, form, wizard_data,
    ):
        return {
            "service_template": template,
            "steps": steps,
            "current_step": current_step,
            "step": step,
            "form": form,
            "wizard_data": wizard_data,
            "is_first_step": current_step == 0,
            "is_last_step": current_step == len(steps) - 1,
            "all_parameters": wizard_data.get("parameters", {}),
            "context_data": wizard_data.get("context", {}),
            "quantity": wizard_data.get("quantity", 1),
        }

    def _get_form_for_step(self, step, wizard_data, data=None):
        if step["type"] == "context":
            initial = wizard_data.get("context", {})
            if data:
                return ContextForm(data, initial=initial)
            return ContextForm(initial=initial)
        elif step["type"] == "params":
            params = step["parameters"]
            initial = {
                k: wizard_data["parameters"][k]
                for p in params
                for k in [p["key"]]
                if k in wizard_data.get("parameters", {})
            }
            if data:
                return ParameterGroupForm(
                    data, parameters=params, initial=initial,
                )
            return ParameterGroupForm(parameters=params, initial=initial)
        elif step["type"] == "summary":
            initial = {"quantity": wizard_data.get("quantity", 1)}
            if data:
                return QuantityForm(data, initial=initial)
            return QuantityForm(initial=initial)
        return forms.Form(data)

    def _submit_order(self, request, template, wizard_data, template_pk):
        try:
            order = OrderService.create_order(
                user=request.user,
                notes=f"{template.name} bestellt",
            )
            OrderService.add_item(
                order_id=order.pk,
                template_id=template.pk,
                parameters=wizard_data.get("parameters", {}),
            )
            self._clear_wizard_data(request, template_pk)
            messages.success(
                request,
                f"Bestellung #{order.pk} erstellt mit {template.name}.",
            )
            return redirect("orders:detail", pk=order.pk)
        except (ValidationError, ConflictError) as e:
            messages.error(request, e.message)
            return redirect("orders:create", template_pk=template_pk)


class OrderFormView(RequesterRequiredMixin, View):
    """Single-page form view — all fields on one page with sidebar summary."""

    def _get_template(self, template_pk):
        try:
            return CatalogService.get_template(template_pk)
        except NotFoundError:
            raise Http404

    def _get_grouped_parameters(self, template):
        """Return parameters grouped by 'group' field, sorted by display_order."""
        groups = {}
        for param in template.parameters:
            group = param.get("group", "Allgemein")
            if group not in groups:
                groups[group] = []
            groups[group].append(param)
        return sorted(
            groups.items(),
            key=lambda g: min(p.get("display_order", 999) for p in g[1]),
        )

    def get(self, request, template_pk):
        template = self._get_template(template_pk)
        form = FullOrderForm(template_parameters=template.parameters)
        grouped = self._get_grouped_parameters(template)
        return render(request, "orders/form_view.html", {
            "service_template": template,
            "form": form,
            "grouped_parameters": grouped,
            "context_fields": ["location", "tenant", "security_zone"],
            "template_parameters_json": template.parameters,
        })

    def post(self, request, template_pk):
        template = self._get_template(template_pk)
        form = FullOrderForm(request.POST, template_parameters=template.parameters)
        grouped = self._get_grouped_parameters(template)

        if not form.is_valid():
            return render(request, "orders/form_view.html", {
                "service_template": template,
                "form": form,
                "grouped_parameters": grouped,
                "context_fields": ["location", "tenant", "security_zone"],
                "template_parameters_json": template.parameters,
            })

        # Extract parameters (exclude context + quantity fields). A context key
        # that is also a real template parameter (e.g. "location") must be kept,
        # otherwise its required value is stripped and validation fails.
        context_keys = {"location", "tenant", "security_zone", "quantity"}
        template_param_keys = {p["key"] for p in template.parameters}
        parameters = {
            k: v for k, v in form.cleaned_data.items()
            if k not in context_keys or k in template_param_keys
        }

        try:
            order = OrderService.create_order(
                user=request.user,
                notes=f"{template.name} bestellt",
            )
            OrderService.add_item(
                order_id=order.pk,
                template_id=template.pk,
                parameters=parameters,
            )
            messages.success(
                request,
                f"Bestellung #{order.pk} erstellt mit {template.name}.",
            )
            return redirect("orders:detail", pk=order.pk)
        except (ValidationError, ConflictError) as e:
            messages.error(request, e.message)
            return render(request, "orders/form_view.html", {
                "service_template": template,
                "form": form,
                "grouped_parameters": grouped,
                "context_fields": ["location", "tenant", "security_zone"],
            })


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
