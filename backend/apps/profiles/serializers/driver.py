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
