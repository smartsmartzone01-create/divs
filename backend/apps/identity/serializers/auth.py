from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.identity.models import Account


class AccountRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=False)
    phone_number = serializers.CharField(required=False, allow_blank=False)

    class Meta:
        model = Account
        fields = ("id", "email", "phone_number", "password", "country_code")
        read_only_fields = ("id",)

    def validate_email(self, value):
        return value.strip().lower() if value else None

    def validate_phone_number(self, value):
        return value.strip() if value else None

    def validate(self, attrs):
        if not attrs.get("email") and not attrs.get("phone_number"):
            raise serializers.ValidationError("Provide an email address or phone number.")
        return attrs

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
            "phone_number",
            "country_code",
            "email_verified",
            "phone_verified",
            "date_joined",
        )
        read_only_fields = fields
