from django.urls import path

from . import views

app_name = "approvals"

urlpatterns = [
    path("", views.ApprovalQueueView.as_view(), name="queue"),
    path(
        "<int:pk>/approve/",
        views.ApprovalApproveView.as_view(),
        name="approve",
    ),
    path(
        "<int:pk>/reject/",
        views.ApprovalRejectView.as_view(),
        name="reject",
    ),
]
