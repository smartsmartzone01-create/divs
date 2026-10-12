from rest_framework import serializers

from apps.profiles.models import ClientProfile
from apps.registrations.serializers import ClientRegistrationSerializer


class ClientProfileSerializer(serializers.ModelSerializer):
    """Return profile lifecycle data with the client's registration details."""

    registration = ClientRegistrationSerializer(read_only=True)

    class Meta:
        model = ClientProfile
        fields = [
            "id",
            "status",
            "registration",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
