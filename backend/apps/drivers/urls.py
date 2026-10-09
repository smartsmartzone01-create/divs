from django.urls import path

from apps.drivers.views import DriverProfileView

app_name = "drivers"

urlpatterns = [
    path("profile/", DriverProfileView.as_view(), name="profile"),
]
