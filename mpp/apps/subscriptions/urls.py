"""URL configuration for the subscriptions app."""
from django.urls import path

from . import views

app_name = "subscriptions"

urlpatterns = [
    path("", views.SubscriptionListView.as_view(), name="list"),
    path(
        "detail/<int:pk>/",
        views.SubscriptionDetailView.as_view(),
        name="detail",
    ),
    path(
        "cancel/<int:pk>/",
        views.SubscriptionCancelView.as_view(),
        name="cancel",
    ),
]
