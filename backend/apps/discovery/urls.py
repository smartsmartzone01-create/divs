from django.urls import path

from apps.discovery.views import PublicDriverDiscoveryView

app_name = "discovery"

urlpatterns = [
    path("drivers/", PublicDriverDiscoveryView.as_view(), name="public-drivers"),
]
