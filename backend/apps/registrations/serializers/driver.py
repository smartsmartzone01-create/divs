from rest_framework import serializers

from apps.registrations.models import DriverRegistration


class DriverRegistrationSerializer(serializers.ModelSerializer):
    contact_email = serializers.EmailField(source="account.email", read_only=True, allow_null=True)
    contact_phone_number = serializers.CharField(source="account.phone_number", read_only=True, allow_null=True)

    class Meta:
        model = DriverRegistration
        fields = [
            "id",
            "first_name",
            "middle_name",
            "last_name",
            "nationality",
            "region",
            "district",
            "current_residential_address",
            "driving_experience",
            "contact_email",
            "contact_phone_number",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "contact_email", "contact_phone_number", "created_at", "updated_at"]

    def validate(self, attrs):
        for field in (
            "first_name", "middle_name", "last_name", "nationality",
            "region", "district", "current_residential_address",
        ):
            if field in attrs and isinstance(attrs[field], str):
                attrs[field] = attrs[field].strip()
        for field in (
            "first_name", "last_name", "nationality", "region", "district",
            "current_residential_address",
        ):
            if field in attrs and not attrs[field]:
                raise serializers.ValidationError({field: "This field cannot be blank."})
        return attrs
