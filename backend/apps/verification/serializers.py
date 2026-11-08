from rest_framework import serializers

from apps.registrations.serializers import DriverRegistrationSerializer
from apps.verification.models import (
    DriverVerification,
    DriverVerificationCheck,
    VerifiedDriverLicenceClass,
    DriverVerificationEvent,
    DriverVerificationEvidence,
    DriverVerificationEvidenceEvent,
)


class VerifiedDriverLicenceClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerifiedDriverLicenceClass
        fields = ["id", "licence_class", "is_current", "verified_at"]
        read_only_fields = fields



class DriverVerificationEvidenceEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverVerificationEvidenceEvent
        fields = ["id", "event_type", "previous_status", "new_status", "notes", "created_at"]
        read_only_fields = fields


class DriverVerificationEvidenceSerializer(serializers.ModelSerializer):
    events = DriverVerificationEvidenceEventSerializer(many=True, read_only=True)

    class Meta:
        model = DriverVerificationEvidence
        fields = [
            "id", "evidence_type", "source", "status", "original_filename",
            "content_type", "file_size", "submitted_at", "reviewed_at",
            "expires_at", "review_notes", "events",
        ]
        read_only_fields = fields


class DriverVerificationCheckSerializer(serializers.ModelSerializer):
    evidence = DriverVerificationEvidenceSerializer(many=True, read_only=True)
    verified_licence_classes = VerifiedDriverLicenceClassSerializer(many=True, read_only=True)

    class Meta:
        model = DriverVerificationCheck
        fields = [
            "id", "check_type", "status", "method", "result_code",
            "review_notes", "checked_at", "reviewed_by",
            "verified_licence_classes", "evidence", "created_at", "updated_at",
        ]
        read_only_fields = fields


class DriverVerificationEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverVerificationEvent
        fields = ["id", "event_type", "previous_status", "new_status", "notes", "actor", "verification_check", "created_at"]
        read_only_fields = fields


class DriverVerificationSerializer(serializers.ModelSerializer):
    checks = DriverVerificationCheckSerializer(many=True, read_only=True)
    is_discoverable = serializers.BooleanField(read_only=True)
    profile_status = serializers.CharField(source="profile.status", read_only=True)
    events = DriverVerificationEventSerializer(many=True, read_only=True)

    class Meta:
        model = DriverVerification
        fields = [
            "id", "status", "checks", "is_discoverable", "profile_status",
            "decision_reason", "decided_by", "decided_at", "events", "created_at", "updated_at",
        ]
        read_only_fields = fields


class OperationsDriverVerificationSerializer(DriverVerificationSerializer):
    registration = DriverRegistrationSerializer(source="profile.registration", read_only=True)
    driver_account_id = serializers.UUIDField(source="profile.registration.account_id", read_only=True)

    class Meta(DriverVerificationSerializer.Meta):
        fields = DriverVerificationSerializer.Meta.fields + ["registration", "driver_account_id"]


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
    review_notes = serializers.CharField(required=False, allow_blank=True, max_length=5000)


class VerificationDecisionSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=5000)


class VerifiedLicenceClassesInputSerializer(serializers.Serializer):
    licence_classes = serializers.ListField(
        child=serializers.RegexField(regex=r"^[A-Za-z0-9]{1,12}$"),
        allow_empty=False,
        min_length=1,
        max_length=20,
    )
