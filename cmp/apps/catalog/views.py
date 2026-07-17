"""Catalog views for browsing service templates."""
from django.http import Http404
from django.views.generic import DetailView, ListView

from core.exceptions import NotFoundError
from core.mixins import RequesterRequiredMixin

from .forms import TemplateFilterForm
from .models import ServiceTemplate
from .services import CatalogService


class TemplateListView(RequesterRequiredMixin, ListView):
    model = ServiceTemplate
    template_name = "catalog/template_list.html"
    context_object_name = "templates"

    def get_queryset(self):
        category = self.request.GET.get("category")
        query = self.request.GET.get("q")
        if query:
            return CatalogService.search_templates(query)
        return CatalogService.list_active_templates(category=category or None)

    def get_template_names(self):
        if self.request.htmx:
            return ["catalog/partials/template_grid.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filter_form"] = TemplateFilterForm(self.request.GET)
        return ctx


class TemplateDetailView(RequesterRequiredMixin, DetailView):
    model = ServiceTemplate
    template_name = "catalog/template_detail.html"
    context_object_name = "template"

    def get_object(self, queryset=None):
        try:
            return CatalogService.get_template(self.kwargs["pk"])
        except NotFoundError:
            raise Http404
