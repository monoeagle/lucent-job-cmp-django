"""URL configuration for the orders app."""
from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("", views.OrderListView.as_view(), name="list"),
    path("<int:pk>/", views.OrderDetailView.as_view(), name="detail"),
    path("create/<int:template_pk>/", views.OrderCreateView.as_view(), name="create"),
    path("<int:pk>/submit/", views.OrderSubmitView.as_view(), name="submit"),
]
