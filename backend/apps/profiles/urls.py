from django.urls import path

from apps.profiles.views import (
    ClientProfileView,
    DriverProfileView,
    OperationsDriverDirectoryView,
    OperationsProfileView,
)

app_name = "profiles"

urlpatterns = [
    path("driver/", DriverProfileView.as_view(), name="driver"),
    path("operations/drivers/", OperationsDriverDirectoryView.as_view(), name="operations-driver-directory"),
    path("client/", ClientProfileView.as_view(), name="client"),
    path("operations/", OperationsProfileView.as_view(), name="operations"),
]
