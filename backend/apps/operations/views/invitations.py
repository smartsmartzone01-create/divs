from django.contrib.auth.hashers import check_password
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.operations.models import OperationsInvitation
from apps.operations.permissions import CanIssueOperationsInvitations
from apps.operations.serializers.invitations import (
    OperationsInvitationCreateSerializer,
    OperationsInvitationValidateSerializer,
)
from apps.operations.services.invitations import (
    InvitationDeliveryError,
    issue_operations_invitation,
)
from apps.operations.throttles import InvitationCodeThrottle


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


class OperationsInvitationValidateView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [InvitationCodeThrottle]

    def post(self, request):
        serializer = OperationsInvitationValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]

        invitation = OperationsInvitation.objects.filter(
            email=email,
            used_at__isnull=True,
            revoked_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).order_by("-created_at").first()

        if invitation is None or not check_password(code, invitation.code_hash):
            return Response(
                {"detail": "The invitation code is invalid, expired, revoked, or already used."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "valid": True,
                "invitation_id": str(invitation.id),
                "email": invitation.email,
                "role": invitation.role,
                "expires_at": invitation.expires_at,
                "detail": "Code accepted. This only allows you to continue an application; it does not grant permissions.",
            },
            status=status.HTTP_200_OK,
        )


class OperationsInvitationRevokeView(APIView):
    permission_classes = [IsAuthenticated, CanIssueOperationsInvitations]

    def post(self, request, invitation_id):
        invitation = OperationsInvitation.objects.filter(pk=invitation_id).first()
        if invitation is None:
            return Response(
                {"detail": "Invitation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if invitation.used_at is not None:
            return Response(
                {"detail": "A used invitation cannot be revoked."},
                status=status.HTTP_409_CONFLICT,
            )
        if invitation.revoked_at is None:
            invitation.revoked_at = timezone.now()
            invitation.save(update_fields=["revoked_at"])

        return Response(
            {"id": str(invitation.id), "revoked": True},
            status=status.HTTP_200_OK,
        )
