from django.urls import path

from apps.profiles.views import DriverProfileView, OperationsProfileView

app_name = "profiles"

urlpatterns = [
    path("driver/", DriverProfileView.as_view(), name="driver"),
    path("operations/", OperationsProfileView.as_view(), name="operations"),
]
