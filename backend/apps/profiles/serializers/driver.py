from rest_framework import serializers

from apps.profiles.models import DriverProfile
from apps.registrations.serializers import DriverRegistrationSerializer


class DriverProfileSerializer(serializers.ModelSerializer):
    """Return profile lifecycle data with the driver's existing registration data."""

    registration = DriverRegistrationSerializer(read_only=True)

    class Meta:
        model = DriverProfile
        fields = [
            "id",
            "status",
            "registration",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class AdminDriverDirectorySerializer(serializers.ModelSerializer):
    """Expose only operationally useful registration and status data to operations."""

    registration = DriverRegistrationSerializer(read_only=True)
    verification_status = serializers.SerializerMethodField()

    class Meta:
        model = DriverProfile
        fields = [
            "id",
            "status",
            "verification_status",
            "registration",
            "created_at",
        ]
        read_only_fields = fields

    def get_verification_status(self, profile):
        try:
            return profile.verification.status
        except DriverProfile.verification.RelatedObjectDoesNotExist:
            return "not_started"
