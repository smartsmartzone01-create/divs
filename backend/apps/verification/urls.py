from django.urls import path

from apps.verification.views import MyDriverVerificationView, OperationsDriverCheckReviewView

app_name = "verification"

urlpatterns = [
    path("driver/me/", MyDriverVerificationView.as_view(), name="driver-me"),
    path(
        "operations/checks/<uuid:check_id>/review/",
        OperationsDriverCheckReviewView.as_view(),
        name="operations-check-review",
    ),
]
