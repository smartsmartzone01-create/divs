from django.urls import path

from apps.notifications.views import (
    ClientNotificationListView,
    DriverNotificationListView,
    OperationsNotificationListView,
)

app_name = "notifications"

urlpatterns = [
    path("driver/", DriverNotificationListView.as_view(), name="driver-list"),
    path(
        "driver/<uuid:notification_id>/read/",
        DriverNotificationListView.as_view(),
        name="driver-read",
    ),
    path("client/", ClientNotificationListView.as_view(), name="client-list"),
    path(
        "client/<uuid:notification_id>/read/",
        ClientNotificationListView.as_view(),
        name="client-read",
    ),
    path("operations/", OperationsNotificationListView.as_view(), name="operations-list"),
    path(
        "operations/<uuid:notification_id>/read/",
        OperationsNotificationListView.as_view(),
        name="operations-read",
    ),
]
