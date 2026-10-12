from django.shortcuts import get_object_or_404
from rest_framework import status as http_status
from rest_framework.response import Response

from apps.profiles.models import DriverProfile
from apps.verification.models import DriverVerification, DriverVerificationCheck
from apps.verification.serializers import (
    DriverVerificationSerializer,
    ManualCheckReviewSerializer,
)
from apps.verification.services import VerificationReviewError, review_driver_check
from common.views import RoleProtectedAPIView


class MyDriverVerificationView(RoleProtectedAPIView):
    """Return the signed-in driver's own verification progress."""

    required_profile_type = "driver"

    def get(self, request):
        profile = get_object_or_404(
            DriverProfile.objects.select_related("registration", "registration__account")
            .prefetch_related("verification__checks"),
            registration__account=request.user,
        )
        verification = get_object_or_404(
            DriverVerification.objects.prefetch_related("checks"),
            profile=profile,
        )
        return Response(DriverVerificationSerializer(verification).data)


class OperationsDriverCheckReviewView(RoleProtectedAPIView):
    """Allow approved operations users to record a minimal manual check outcome."""

    required_profile_type = "operations"

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
