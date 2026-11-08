from django.urls import path

from apps.verification.views import (
    MyDriverVerificationView,
    OperationsDriverAvailabilityActivateView,
    OperationsDriverCheckReviewView,
    OperationsVerificationEvidenceReviewView,
    OperationsDriverVerificationApproveView,
    OperationsDriverVerificationRejectView,
    OperationsVerificationDetailView,
    OperationsVerificationQueueView,
    OperationsVerifiedLicenceClassesView,
    DriverVerificationEvidenceUploadView,
    OperationsVerificationEvidenceUploadView,
    DriverVerificationEvidenceFileView,
    OperationsVerificationEvidenceFileView,
)

app_name = "verification"

urlpatterns = [
    path("driver/me/", MyDriverVerificationView.as_view(), name="driver-me"),
    path("driver/checks/<uuid:check_id>/evidence/", DriverVerificationEvidenceUploadView.as_view(), name="driver-evidence-upload"),
    path("driver/evidence/<uuid:evidence_id>/file/", DriverVerificationEvidenceFileView.as_view(), name="driver-evidence-file"),
    path("operations/queue/", OperationsVerificationQueueView.as_view(), name="operations-verification-queue"),
    path("operations/checks/<uuid:check_id>/evidence/", OperationsVerificationEvidenceUploadView.as_view(), name="operations-evidence-upload"),
    path("operations/evidence/<uuid:evidence_id>/file/", OperationsVerificationEvidenceFileView.as_view(), name="operations-evidence-file"),
    path("operations/evidence/<uuid:evidence_id>/review/", OperationsVerificationEvidenceReviewView.as_view(), name="operations-evidence-review"),
    path("operations/<uuid:verification_id>/", OperationsVerificationDetailView.as_view(), name="operations-verification-detail"),
    path("operations/<uuid:verification_id>/approve/", OperationsDriverVerificationApproveView.as_view(), name="operations-verification-approve"),
    path("operations/<uuid:verification_id>/reject/", OperationsDriverVerificationRejectView.as_view(), name="operations-verification-reject"),
    path("operations/<uuid:verification_id>/activate/", OperationsDriverAvailabilityActivateView.as_view(), name="operations-driver-activate"),
    path("operations/checks/<uuid:check_id>/review/", OperationsDriverCheckReviewView.as_view(), name="operations-check-review"),
    path("operations/checks/<uuid:check_id>/licence-classes/", OperationsVerifiedLicenceClassesView.as_view(), name="operations-verified-licence-classes"),
]
