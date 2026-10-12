from django.urls import path

from apps.notifications.views import (
    ClientNotificationListView,
    ClientNotificationReadView,
    DriverNotificationListView,
    DriverNotificationReadView,
    OperationsNotificationListView,
    OperationsNotificationReadView,
)

app_name = "notifications"

urlpatterns = [
    path("driver/", DriverNotificationListView.as_view(), name="driver-list"),
    path(
        "driver/<uuid:notification_id>/read/",
        DriverNotificationReadView.as_view(),
        name="driver-read",
    ),
    path("client/", ClientNotificationListView.as_view(), name="client-list"),
    path(
        "client/<uuid:notification_id>/read/",
        ClientNotificationReadView.as_view(),
        name="client-read",
    ),
    path("operations/", OperationsNotificationListView.as_view(), name="operations-list"),
    path(
        "operations/<uuid:notification_id>/read/",
        OperationsNotificationReadView.as_view(),
        name="operations-read",
    ),
]
