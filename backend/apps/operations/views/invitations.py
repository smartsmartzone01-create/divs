from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.operations.permissions import CanIssueOperationsInvitations
from apps.operations.serializers.invitations import OperationsInvitationCreateSerializer
from apps.operations.services.invitations import (
    InvitationDeliveryError,
    issue_operations_invitation,
)


class OperationsInvitationCreateView(APIView):
    permission_classes = [IsAuthenticated, CanIssueOperationsInvitations]

    def post(self, request):
        serializer = OperationsInvitationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            invitation = issue_operations_invitation(
                inviter=request.user,
                email=serializer.validated_data["email"],
                role=serializer.validated_data["role"],
            )
        except InvitationDeliveryError:
            return Response(
                {"detail": "The invitation could not be sent. No active invitation was created."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "id": str(invitation.id),
                "email": invitation.email,
                "role": invitation.role,
                "expires_at": invitation.expires_at,
                "detail": "Invitation email sent. The recipient must apply and be approved separately.",
            },
            status=status.HTTP_201_CREATED,
        )
