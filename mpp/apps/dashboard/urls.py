from django.urls import path
from django.views.generic import TemplateView
from . import views
from . import admin_views

app_name = "dashboard"
urlpatterns = [
    path("", views.DashboardView.as_view(), name="home"),
    path("debug-layout/", TemplateView.as_view(template_name="debug_layout.html"), name="debug_layout"),
    path(
        "admin-panel/",
        admin_views.AdminDashboardView.as_view(),
        name="admin_dashboard",
    ),
    path(
        "admin-panel/config/",
        admin_views.AdminConfigView.as_view(),
        name="admin_config",
    ),
    path(
        "admin-panel/rules/",
        admin_views.AdminRulesView.as_view(),
        name="admin_rules",
    ),
]
