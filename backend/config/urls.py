from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.identity.urls")),
    path("api/v1/registrations/", include("apps.registrations.urls")),
    path("api/v1/profiles/", include("apps.profiles.urls")),
    path("api/v1/operations/", include("apps.operations.urls")),
    path("api/v1/verification/", include("apps.verification.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
]
