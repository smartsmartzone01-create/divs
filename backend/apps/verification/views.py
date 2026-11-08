from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status as http_status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from apps.profiles.models import DriverProfile
from apps.verification.models import DriverVerification, DriverVerificationCheck, DriverVerificationEvidence
from apps.verification.serializers import (
    DriverVerificationSerializer,
    ManualCheckReviewSerializer,
    OperationsDriverVerificationSerializer,
    VerificationDecisionSerializer,
    VerifiedLicenceClassesInputSerializer,
    DriverVerificationEvidenceSerializer,
    VerificationEvidenceUploadSerializer,
)
from apps.verification.services import (
    VerificationReviewError,
    activate_driver_availability,
    decide_driver_verification,
    record_verified_licence_classes,
    review_driver_check,
)
from apps.verification.storage import (
    EvidenceStorageError,
    retrieve_verification_evidence,
    store_verification_evidence,
)
from apps.operations.permissions import HasOperationsCapability
from common.permissions import HasRequiredProfile
from common.views import RoleProtectedAPIView


class MyDriverVerificationView(RoleProtectedAPIView):
    required_profile_type = "driver"

    def get(self, request):
        profile = get_object_or_404(
            DriverProfile.objects.select_related("registration", "registration__account")
            .prefetch_related("verification__checks__verified_licence_classes"),
            registration__account=request.user,
        )
        verification = get_object_or_404(
            DriverVerification.objects.prefetch_related("checks__verified_licence_classes"),
            profile=profile,
        )
        return Response(DriverVerificationSerializer(verification).data)


class OperationsVerificationQueueView(RoleProtectedAPIView):
    required_profile_type = "operations"
    required_operations_capability = "view_operations_workspace"
    permission_classes = [IsAuthenticated, HasRequiredProfile, HasOperationsCapability]

    def get(self, request):
        items = (
            DriverVerification.objects.filter(
                status__in=[DriverVerification.Status.PENDING, DriverVerification.Status.IN_REVIEW]
            )
            .select_related("profile", "profile__registration", "profile__registration__account")
            .prefetch_related("checks__verified_licence_classes", "events")
            .order_by("created_at")
        )
        return Response({
            "count": items.count(),
            "results": OperationsDriverVerificationSerializer(items, many=True).data,
        })


class OperationsVerificationDetailView(RoleProtectedAPIView):
    required_profile_type = "operations"
    required_operations_capability = "view_operations_workspace"
    permission_classes = [IsAuthenticated, HasRequiredProfile, HasOperationsCapability]

    def get(self, request, verification_id):
        verification = get_object_or_404(
            DriverVerification.objects.select_related(
                "profile", "profile__registration", "profile__registration__account"
            ).prefetch_related("checks__verified_licence_classes", "events"),
            pk=verification_id,
        )
        return Response(OperationsDriverVerificationSerializer(verification).data)


class OperationsDriverCheckReviewView(RoleProtectedAPIView):
    required_profile_type = "operations"
    required_operations_capability = "review_driver_verification"
    permission_classes = [IsAuthenticated, HasRequiredProfile, HasOperationsCapability]

    def post(self, request, check_id):
        serializer = ManualCheckReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            check = review_driver_check(
                check_id=check_id,
                reviewer=request.user,
                status=serializer.validated_data["status"],
                result_code=serializer.validated_data.get("result_code", ""),
                review_notes=serializer.validated_data.get("review_notes", ""),
            )
        except VerificationReviewError as exc:
            return Response({"detail": str(exc)}, status=http_status.BAD_REQUEST)
        return Response({
            "id": str(check.id), "check_type": check.check_type,
            "status": check.status, "method": check.method,
            "result_code": check.result_code, "review_notes": check.review_notes,
            "checked_at": check.checked_at,
        })


class OperationsVerifiedLicenceClassesView(RoleProtectedAPIView):
    required_profile_type = "operations"
    required_operations_capability = "review_driver_verification"
    permission_classes = [IsAuthenticated, HasRequiredProfile, HasOperationsCapability]

    def post(self, request, check_id):
        serializer = VerifiedLicenceClassesInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            records = record_verified_licence_classes(
                check_id=check_id,
                licence_classes=serializer.validated_data["licence_classes"],
                reviewer=request.user,
            )
        except VerificationReviewError as exc:
            return Response({"detail": str(exc)}, status=http_status.BAD_REQUEST)
        return Response([
            {
                "id": str(record.id), "licence_class": record.licence_class,
                "is_current": record.is_current, "verified_at": record.verified_at,
            }
            for record in records
        ])


class _OperationsFinalDecisionView(RoleProtectedAPIView):
    required_profile_type = "operations"
    permission_classes = [IsAuthenticated, HasRequiredProfile, HasOperationsCapability]
    decision = None

    def post(self, request, verification_id):
        serializer = VerificationDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            verification = decide_driver_verification(
                verification_id=verification_id,
                actor=request.user,
                decision=self.decision,
                reason=serializer.validated_data.get("reason", ""),
            )
        except VerificationReviewError as exc:
            return Response({"detail": str(exc)}, status=http_status.BAD_REQUEST)
        return Response(OperationsDriverVerificationSerializer(verification).data)


class OperationsDriverVerificationApproveView(_OperationsFinalDecisionView):
    required_operations_capability = "approve_driver_verification"
    decision = DriverVerification.Status.APPROVED


class OperationsDriverVerificationRejectView(_OperationsFinalDecisionView):
    required_operations_capability = "reject_driver_verification"
    decision = DriverVerification.Status.REJECTED


class OperationsDriverAvailabilityActivateView(RoleProtectedAPIView):
    required_profile_type = "operations"
    required_operations_capability = "activate_driver_availability"
    permission_classes = [IsAuthenticated, HasRequiredProfile, HasOperationsCapability]

    def post(self, request, verification_id):
        try:
            profile = activate_driver_availability(
                verification_id=verification_id,
                actor=request.user,
            )
        except VerificationReviewError as exc:
            return Response({"detail": str(exc)}, status=http_status.BAD_REQUEST)
        return Response({
            "driver_profile_id": str(profile.id),
            "status": profile.status,
        }, status=http_status.OK)



def _evidence_file_response(evidence):
    try:
        body, content_type, _filename = retrieve_verification_evidence(evidence)
    except EvidenceStorageError as exc:
        return Response({"detail": str(exc)}, status=http_status.SERVICE_UNAVAILABLE)

    def file_chunks():
        try:
            while True:
                chunk = body.read(64 * 1024)
                if not chunk:
                    break
                yield chunk
        finally:
            body.close()

    response = StreamingHttpResponse(file_chunks(), content_type=content_type)
    response["Content-Disposition"] = 'inline; filename="verification-evidence"'
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Security-Policy"] = "sandbox; default-src 'none'"
    return response


class DriverVerificationEvidenceUploadView(RoleProtectedAPIView):
    required_profile_type = "driver"
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "verification_evidence_upload"

    def post(self, request, check_id):
        check = get_object_or_404(
            DriverVerificationCheck.objects.select_related("verification", "verification__profile"),
            pk=check_id,
            verification__profile__registration__account=request.user,
        )
        serializer = VerificationEvidenceUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            evidence = store_verification_evidence(
                check=check,
                uploaded_file=serializer.validated_data["file"],
                actor=request.user,
                source=DriverVerificationEvidence.Source.DRIVER_UPLOAD,
            )
        except EvidenceStorageError as exc:
            return Response({"detail": str(exc)}, status=http_status.BAD_REQUEST)
        return Response(DriverVerificationEvidenceSerializer(evidence).data, status=http_status.CREATED)


class OperationsVerificationEvidenceUploadView(RoleProtectedAPIView):
    required_profile_type = "operations"
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "verification_evidence_upload"
    required_operations_capability = "review_driver_verification"
    permission_classes = [IsAuthenticated, HasRequiredProfile, HasOperationsCapability]

    def post(self, request, check_id):
        check = get_object_or_404(
            DriverVerificationCheck.objects.select_related("verification", "verification__profile"),
            pk=check_id,
        )
        serializer = VerificationEvidenceUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            evidence = store_verification_evidence(
                check=check,
                uploaded_file=serializer.validated_data["file"],
                actor=request.user,
                source=DriverVerificationEvidence.Source.OPERATIONS_UPLOAD,
            )
        except EvidenceStorageError as exc:
            return Response({"detail": str(exc)}, status=http_status.BAD_REQUEST)
        return Response(DriverVerificationEvidenceSerializer(evidence).data, status=http_status.CREATED)


class DriverVerificationEvidenceFileView(RoleProtectedAPIView):
    required_profile_type = "driver"

    def get(self, request, evidence_id):
        evidence = get_object_or_404(
            DriverVerificationEvidence.objects.select_related("verification_check__verification__profile"),
            pk=evidence_id,
            verification_check__verification__profile__registration__account=request.user,
        )
        return _evidence_file_response(evidence)


class OperationsVerificationEvidenceFileView(RoleProtectedAPIView):
    required_profile_type = "operations"
    required_operations_capability = "review_driver_verification"
    permission_classes = [IsAuthenticated, HasRequiredProfile, HasOperationsCapability]

    def get(self, request, evidence_id):
        evidence = get_object_or_404(
            DriverVerificationEvidence.objects.select_related("verification_check__verification__profile"),
            pk=evidence_id,
        )
        return _evidence_file_response(evidence)
