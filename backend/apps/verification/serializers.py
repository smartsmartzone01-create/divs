from rest_framework import serializers

from apps.verification.models import DriverVerification, DriverVerificationCheck


class DriverVerificationCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverVerificationCheck
        fields = [
            "id", "check_type", "status", "method", "result_code",
            "checked_at", "created_at", "updated_at",
        ]
        read_only_fields = fields


class DriverVerificationSerializer(serializers.ModelSerializer):
    checks = DriverVerificationCheckSerializer(many=True, read_only=True)
    is_discoverable = serializers.BooleanField(read_only=True)

    class Meta:
        model = DriverVerification
        fields = [
            "id", "status", "checks", "is_discoverable",
            "decided_at", "created_at", "updated_at",
        ]
        read_only_fields = fields


class ManualCheckReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[
            DriverVerificationCheck.Status.PASSED,
            DriverVerificationCheck.Status.FAILED,
            DriverVerificationCheck.Status.NEEDS_REVIEW,
            DriverVerificationCheck.Status.UNAVAILABLE,
        ]
    )
    result_code = serializers.ChoiceField(
        choices=DriverVerificationCheck.ResultCode.choices,
        required=False,
        allow_blank=True,
    )
    review_note = serializers.CharField(required=False, allow_blank=True, max_length=500)
