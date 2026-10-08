from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.identity.models import Account


class AccountRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    email = serializers.EmailField()

    class Meta:
        model = Account
        fields = ("id", "email", "username", "password", "phone_number", "country_code")
        read_only_fields = ("id",)

    def validate_email(self, value):
        return value.strip().lower()

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        return Account.objects.create_user(password=password, **validated_data)


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = (
            "id",
            "email",
            "username",
            "phone_number",
            "country_code",
            "email_verified",
            "phone_verified",
            "date_joined",
        )
        read_only_fields = fields
