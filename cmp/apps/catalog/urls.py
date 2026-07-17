"""Catalog URL configuration."""
from django.urls import path

from . import views

app_name = "catalog"
urlpatterns = [
    path("", views.TemplateListView.as_view(), name="list"),
    path("<int:pk>/", views.TemplateDetailView.as_view(), name="detail"),
]
