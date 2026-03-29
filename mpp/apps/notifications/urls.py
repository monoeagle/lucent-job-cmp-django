from django.urls import path

from . import views

app_name = "notifications"
urlpatterns = [
    path("", views.NotificationListView.as_view(), name="list"),
    path(
        "mark-read/<int:pk>/",
        views.NotificationMarkReadView.as_view(),
        name="mark_read",
    ),
    path(
        "mark-all-read/",
        views.NotificationMarkAllReadView.as_view(),
        name="mark_all_read",
    ),
]
