"""URL configuration for the orders app."""
from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("", views.OrderListView.as_view(), name="list"),
    path("<int:pk>/", views.OrderDetailView.as_view(), name="detail"),
    path("create/<int:template_pk>/", views.OrderCreateView.as_view(), name="create"),
    path("create/<int:template_pk>/form/", views.OrderFormView.as_view(), name="create_form"),
    path("<int:pk>/add-item/<int:template_pk>/", views.OrderAddItemView.as_view(), name="add_item"),
    path("<int:pk>/remove-item/<int:item_pk>/", views.OrderRemoveItemView.as_view(), name="remove_item"),
    path("<int:pk>/submit/", views.OrderSubmitView.as_view(), name="submit"),
]
