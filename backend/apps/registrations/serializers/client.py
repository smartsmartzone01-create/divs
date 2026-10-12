from rest_framework import serializers

from apps.registrations.models import ClientRegistration


class ClientRegistrationSerializer(serializers.ModelSerializer):
    alternative_contacts = serializers.ListField(
        child=serializers.CharField(max_length=200, allow_blank=False),
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = ClientRegistration
        fields = [
            "id",
            "client_type",
            "name",
            "primary_contact",
            "email",
            "country",
            "region",
            "alternative_contacts",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        for field in ("name", "primary_contact", "email", "country", "region"):
            if field in attrs and isinstance(attrs[field], str):
                attrs[field] = attrs[field].strip()
                if not attrs[field]:
                    raise serializers.ValidationError(
                        {field: "This field cannot be blank."}
                    )

        if "alternative_contacts" in attrs:
            contacts = [contact.strip() for contact in attrs["alternative_contacts"]]
            if any(not contact for contact in contacts):
                raise serializers.ValidationError(
                    {"alternative_contacts": "Contacts cannot be blank."}
                )
            attrs["alternative_contacts"] = contacts
        return attrs
