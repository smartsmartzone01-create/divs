from rest_framework import serializers

from apps.operations.models import OperationsInvitation


class OperationsInvitationCreateSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    role = serializers.ChoiceField(choices=OperationsInvitation.Role.choices)

    def validate_email(self, value):
        return value.strip().lower()
