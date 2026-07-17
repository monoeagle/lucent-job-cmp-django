from django.views.generic import TemplateView
from core.mixins import RequesterRequiredMixin


class ProfileView(RequesterRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"
