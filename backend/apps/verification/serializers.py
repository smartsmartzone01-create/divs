from rest_framework import serializers

from apps.verification.models import (
    DriverVerification,
    DriverVerificationCheck,
    VerifiedDriverLicenceClass,
)


class VerifiedDriverLicenceClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerifiedDriverLicenceClass
        fields = ["id", "licence_class", "is_current", "verified_at"]
        read_only_fields = fields


class DriverVerificationCheckSerializer(serializers.ModelSerializer):
    verified_licence_classes = VerifiedDriverLicenceClassSerializer(many=True, read_only=True)

    class Meta:
        model = DriverVerificationCheck
        fields = [
            "id", "check_type", "status", "method", "result_code",
            "checked_at", "verified_licence_classes", "created_at", "updated_at",
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


class VerifiedLicenceClassesInputSerializer(serializers.Serializer):
    licence_classes = serializers.ListField(
        child=serializers.RegexField(regex=r"^[A-Za-z0-9]{1,12}$"),
        allow_empty=False,
        min_length=1,
        max_length=20,
    )
