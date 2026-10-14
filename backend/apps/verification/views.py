from django.shortcuts import get_object_or_404
from rest_framework import status as http_status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.profiles.models import DriverProfile
from apps.verification.models import DriverVerification, DriverVerificationCheck
from apps.verification.serializers import (
    DriverVerificationSerializer,
    ManualCheckReviewSerializer,
    VerifiedLicenceClassesInputSerializer,
)
from apps.verification.services import (
    VerificationReviewError,
    record_verified_licence_classes,
    review_driver_check,
)
from apps.operations.permissions import HasOperationsCapability
from common.permissions import HasRequiredProfile
from common.views import RoleProtectedAPIView


class MyDriverVerificationView(RoleProtectedAPIView):
    """Return the signed-in driver's own verification progress."""

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


class OperationsDriverCheckReviewView(RoleProtectedAPIView):
    """Allow authorized operations members to record a minimal manual check outcome."""

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
            )
        except VerificationReviewError as exc:
            return Response({"detail": str(exc)}, status=http_status.BAD_REQUEST)
        return Response(
            {
                "id": str(check.id),
                "check_type": check.check_type,
                "status": check.status,
                "method": check.method,
                "result_code": check.result_code,
                "checked_at": check.checked_at,
            },
            status=http_status.OK,
        )


class OperationsVerifiedLicenceClassesView(RoleProtectedAPIView):
    """Record licence classes only after the existing licence check passed validation."""

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
        return Response(
            [
                {
                    "id": str(record.id),
                    "licence_class": record.licence_class,
                    "is_current": record.is_current,
                    "verified_at": record.verified_at,
                }
                for record in records
            ],
            status=http_status.OK,
        )
