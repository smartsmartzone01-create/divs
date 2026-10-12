from django.urls import path

from apps.registrations.views import ClientRegistrationView, DriverRegistrationView

app_name = "registrations"

urlpatterns = [
    path("driver/", DriverRegistrationView.as_view(), name="driver"),
    path("client/", ClientRegistrationView.as_view(), name="client"),
]
