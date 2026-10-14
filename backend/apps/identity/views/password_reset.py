import logging

from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.identity.models import AuthSession, VerificationCode
from apps.identity.services.verification import issue_verification_code, verify_code
from common.throttles.authentication import (
    VerificationConfirmThrottle,
    VerificationRequestThrottle,
    VerificationResendCooldownThrottle,
)


logger = logging.getLogger(__name__)
Account = get_user_model()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [
        VerificationRequestThrottle,
        VerificationResendCooldownThrottle,
    ]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()
        account = Account.objects.filter(
            email__iexact=email,
            email_verified=True,
            is_active=True,
        ).first()

        # Keep the response identical for unknown addresses and delivery failures so this
        # endpoint cannot be used to enumerate registered email addresses.
        if account is not None:
            try:
                issue_verification_code(
                    VerificationCode.Channel.EMAIL,
                    email,
                    account=account,
                    purpose=VerificationCode.Purpose.PASSWORD_RESET,
                )
            except Exception as exc:
                # Avoid logging the recipient address or provider exception details.
                logger.warning("Password reset email delivery failed (%s).", type(exc).__name__)
        return Response(
            {"detail": "If an active account with a verified email exists, reset instructions will be sent."},
            status=status.HTTP_202_ACCEPTED,
        )


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.RegexField(r"^\d{6}$")
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_new_password(self, value):
        try:
            password_validation.validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return value


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [VerificationConfirmThrottle]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        email = data["email"].strip().lower()

        with transaction.atomic():
            if not verify_code(
                VerificationCode.Channel.EMAIL,
                email,
                data["code"],
                purpose=VerificationCode.Purpose.PASSWORD_RESET,
            ):
                return Response(
                    {"detail": "The reset code is invalid, expired, or no longer usable."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            account = Account.objects.filter(
                email__iexact=email,
                email_verified=True,
                is_active=True,
            ).first()
            if account is None:
                return Response(
                    {"detail": "The reset code is invalid, expired, or no longer usable."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                password_validation.validate_password(data["new_password"], user=account)
            except DjangoValidationError as exc:
                # Raising inside the transaction rolls back consumption of the valid code.
                raise serializers.ValidationError({"new_password": exc.messages}) from exc
            account.set_password(data["new_password"])
            account.save(update_fields=["password", "updated_at"])
            # Session JWT authentication checks this record on every request, so revoking
            # sessions immediately invalidates existing access and refresh tokens.
            AuthSession.objects.filter(
                account=account,
                revoked_at__isnull=True,
            ).update(revoked_at=timezone.now())

        return Response(
            {"detail": "Password reset successfully. Sign in again with your new password."},
            status=status.HTTP_200_OK,
        )
