from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.identity.models import Account, VerificationCode
from apps.identity.services.verification import (
    VerificationDeliveryNotConfigured,
    issue_verification_code,
    verify_code,
)
from common.throttles.authentication import (
    VerificationRequestThrottle,
    VerificationResendCooldownThrottle,
)


class VerificationRequestSerializer(serializers.Serializer):
    channel = serializers.ChoiceField(choices=VerificationCode.Channel.choices)
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False, max_length=32)

    def validate(self, attrs):
        channel = attrs["channel"]
        if channel == VerificationCode.Channel.EMAIL and not attrs.get("email"):
            raise serializers.ValidationError({"email": "An email address is required for email verification."})
        if channel == VerificationCode.Channel.PHONE and not attrs.get("phone_number"):
            raise serializers.ValidationError({"phone_number": "A phone number is required for phone verification."})
        return attrs


class VerificationRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [VerificationRequestThrottle, VerificationResendCooldownThrottle]

    def post(self, request):
        serializer = VerificationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        channel = data["channel"]
        target = data.get("email") or data.get("phone_number")
        lookup = {"email__iexact": target} if channel == VerificationCode.Channel.EMAIL else {"phone_number": target}
        account = Account.objects.filter(**lookup).first()
        try:
            issue_verification_code(channel, target, account=account)
        except VerificationDeliveryNotConfigured as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception:
            # Do not expose mail-provider errors or account existence to callers.
            return Response(
                {"detail": "Verification delivery is temporarily unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(
            {"detail": "If this destination can be verified, a code has been sent."},
            status=status.HTTP_202_ACCEPTED,
        )


class VerificationConfirmSerializer(serializers.Serializer):
    channel = serializers.ChoiceField(choices=VerificationCode.Channel.choices)
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False, max_length=32)
    code = serializers.RegexField(r"^\d{6}$")

    def validate(self, attrs):
        channel = attrs["channel"]
        if channel == VerificationCode.Channel.EMAIL and not attrs.get("email"):
            raise serializers.ValidationError({"email": "An email address is required."})
        if channel == VerificationCode.Channel.PHONE and not attrs.get("phone_number"):
            raise serializers.ValidationError({"phone_number": "A phone number is required."})
        return attrs


class VerificationConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerificationConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        channel = data["channel"]
        target = data.get("email") or data.get("phone_number")
        if not verify_code(channel, target, data["code"]):
            return Response(
                {"detail": "The code is invalid, expired, or no longer usable."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        lookup = {"email__iexact": target} if channel == VerificationCode.Channel.EMAIL else {"phone_number": target}
        account = Account.objects.filter(**lookup).first()
        if account:
            field = "email_verified" if channel == VerificationCode.Channel.EMAIL else "phone_verified"
            setattr(account, field, True)
            account.save(update_fields=[field, "updated_at"])
        return Response({"verified": True}, status=status.HTTP_200_OK)
