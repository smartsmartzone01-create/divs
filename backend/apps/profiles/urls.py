from django.urls import path

from apps.profiles.views import DriverProfileView

app_name = "profiles"

urlpatterns = [
    path("driver/", DriverProfileView.as_view(), name="driver"),
]
