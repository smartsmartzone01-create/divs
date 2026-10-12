from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.operations.models import OperationsApplication
from apps.operations.serializers.reviews import OperationsApplicationReviewSerializer
from apps.operations.services.reviews import (
    ApplicationReviewError,
    review_operations_application,
)


class SystemSuperuserOnly:
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class OperationsApplicationPendingListView(APIView):
    permission_classes = [IsAuthenticated, SystemSuperuserOnly]

    def get(self, request):
        applications = OperationsApplication.objects.filter(
            status=OperationsApplication.Status.PENDING,
        ).select_related("account", "invitation")
        return Response([
            {
                "id": str(application.id),
                "full_name": application.full_name,
                "email": application.account.email,
                "phone_number": application.account.phone_number,
                "role_applied_for": application.invitation.role,
                "submitted_at": application.submitted_at,
            }
            for application in applications
        ])


class OperationsApplicationReviewView(APIView):
    permission_classes = [IsAuthenticated, SystemSuperuserOnly]

    def post(self, request, application_id):
        serializer = OperationsApplicationReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            application = review_operations_application(
                application_id=application_id,
                reviewer=request.user,
                decision=serializer.validated_data["decision"],
                review_note=serializer.validated_data.get("review_note", ""),
            )
        except ApplicationReviewError:
            return Response(
                {"detail": "This application cannot be reviewed. It may not exist or may already be decided."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {
                "id": str(application.id),
                "status": application.status,
                "reviewed_at": application.reviewed_at,
                "detail": (
                    "Application approved and role activated."
                    if application.status == OperationsApplication.Status.APPROVED
                    else "Application rejected."
                ),
            },
            status=status.HTTP_200_OK,
        )
