from django.urls import path

from apps.verification.views import (
    MyDriverVerificationView,
    OperationsDriverCheckReviewView,
    OperationsVerifiedLicenceClassesView,
)

app_name = "verification"

urlpatterns = [
    path("driver/me/", MyDriverVerificationView.as_view(), name="driver-me"),
    path(
        "operations/checks/<uuid:check_id>/review/",
        OperationsDriverCheckReviewView.as_view(),
        name="operations-check-review",
    ),
    path(
        "operations/checks/<uuid:check_id>/licence-classes/",
        OperationsVerifiedLicenceClassesView.as_view(),
        name="operations-verified-licence-classes",
    ),
]
