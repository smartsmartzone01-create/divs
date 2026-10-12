from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.operations.serializers.applications import OperationsApplicationCreateSerializer
from apps.operations.services.applications import (
    InvalidOperationsInvitation,
    submit_operations_application,
)


class OperationsApplicationCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OperationsApplicationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            application = submit_operations_application(
                account=request.user,
                invitation_id=data["invitation_id"],
                code=data["code"],
                full_name=data["full_name"],
            )
        except InvalidOperationsInvitation:
            return Response(
                {"detail": "The invitation is invalid, expired, revoked, or already used for this email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "id": str(application.id),
                "full_name": application.full_name,
                "email": request.user.email,
                "role_applied_for": application.invitation.role,
                "status": application.status,
                "submitted_at": application.submitted_at,
                "detail": "Application submitted for review. No operations permissions have been granted.",
            },
            status=status.HTTP_201_CREATED,
        )
