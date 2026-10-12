from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.operations.models import OperationsApplication


class OperationsApplicationMyStatusView(APIView):
    """Return only the authenticated applicant's latest application status."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        application = (
            OperationsApplication.objects.filter(account=request.user)
            .select_related("invitation")
            .order_by("-submitted_at")
            .first()
        )
        if application is None:
            return Response(
                {"has_application": False, "detail": "No operations application was found for this account."},
                status=200,
            )

        return Response(
            {
                "has_application": True,
                "id": str(application.id),
                "full_name": application.full_name,
                "role_applied_for": application.invitation.role,
                "status": application.status,
                "submitted_at": application.submitted_at,
                "reviewed_at": application.reviewed_at,
                "detail": {
                    OperationsApplication.Status.PENDING: "Your application is waiting for review.",
                    OperationsApplication.Status.APPROVED: "Your application was approved.",
                    OperationsApplication.Status.REJECTED: "Your application was not approved.",
                }[application.status],
            },
            status=200,
        )
