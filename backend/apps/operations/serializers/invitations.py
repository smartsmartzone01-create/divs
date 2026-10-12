from rest_framework import serializers

from apps.operations.models import OperationsInvitation


class OperationsInvitationCreateSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    role = serializers.ChoiceField(choices=OperationsInvitation.Role.choices)

    def validate_email(self, value):
        return value.strip().lower()


class OperationsInvitationValidateSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    code = serializers.CharField(max_length=128, trim_whitespace=True)

    def validate_email(self, value):
        return value.strip().lower()

    def validate_code(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Enter the invitation code.")
        return value
