from django.shortcuts import get_object_or_404
from rest_framework import status as http_status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.profiles.models import DriverProfile
from apps.verification.models import DriverVerification, DriverVerificationCheck
from apps.verification.serializers import (
    DriverVerificationSerializer,
    ManualCheckReviewSerializer,
    OperationsDriverVerificationSerializer,
    VerificationDecisionSerializer,
    VerifiedLicenceClassesInputSerializer,
)
from apps.verification.services import (
    VerificationReviewError,
    activate_driver_availability,
    decide_driver_verification,
    record_verified_licence_classes,
    review_driver_check,
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
