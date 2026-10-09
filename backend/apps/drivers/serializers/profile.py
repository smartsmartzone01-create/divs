from rest_framework import serializers

from apps.drivers.models import DriverProfile


class DriverProfileSerializer(serializers.ModelSerializer):
    contact_email = serializers.SerializerMethodField()
    contact_phone_number = serializers.SerializerMethodField()
    is_eligible_to_work = serializers.BooleanField(read_only=True)

    class Meta:
        model = DriverProfile
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
            "verification_status",
            "is_eligible_to_work",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "contact_email",
            "contact_phone_number",
            "verification_status",
            "is_eligible_to_work",
            "created_at",
            "updated_at",
        ]

    def get_contact_email(self, obj):
        return obj.account.email or None

    def get_contact_phone_number(self, obj):
        return obj.account.phone_number or None

    def validate(self, attrs):
        for field in (
            "first_name",
            "middle_name",
            "last_name",
            "nationality",
            "region",
            "district",
            "current_residential_address",
        ):
            if field in attrs and isinstance(attrs[field], str):
                attrs[field] = attrs[field].strip()

        for field in (
            "first_name",
            "last_name",
            "nationality",
            "region",
            "district",
            "current_residential_address",
        ):
            if field in attrs and not attrs[field]:
                raise serializers.ValidationError({field: "This field cannot be blank."})

        return attrs
