from rest_framework import serializers

from apps.operations.models import OperationsApplication


class OperationsApplicationCreateSerializer(serializers.Serializer):
    invitation_id = serializers.UUIDField()
    code = serializers.CharField(max_length=128, trim_whitespace=True)
    full_name = serializers.CharField(max_length=200, trim_whitespace=True)

    def validate_full_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Enter your full name.")
        return value
