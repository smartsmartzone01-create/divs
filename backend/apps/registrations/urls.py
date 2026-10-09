from django.urls import path

from apps.registrations.views import DriverRegistrationView

app_name = "registrations"

urlpatterns = [
    path("driver/", DriverRegistrationView.as_view(), name="driver"),
]
