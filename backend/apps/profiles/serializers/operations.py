from rest_framework import serializers

from apps.operations.models import OperationsApplication
from apps.profiles.models import OperationsProfile


class OperationsProfileSerializer(serializers.ModelSerializer):
    """Return the signed-in operations member's own profile and approved role."""

    full_name = serializers.SerializerMethodField()
    role = serializers.CharField(source="membership.role", read_only=True)
    email = serializers.EmailField(source="membership.account.email", read_only=True)
    phone_number = serializers.CharField(
        source="membership.account.phone_number",
        read_only=True,
        allow_null=True,
    )
    approved_at = serializers.DateTimeField(source="membership.approved_at", read_only=True)

    class Meta:
        model = OperationsProfile
        fields = [
            "id",
            "status",
            "full_name",
            "role",
            "email",
            "phone_number",
            "approved_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_full_name(self, profile):
        application = (
            OperationsApplication.objects.filter(
                account_id=profile.membership.account_id,
                status=OperationsApplication.Status.APPROVED,
            )
            .order_by("-reviewed_at", "-submitted_at")
            .only("full_name")
            .first()
        )
        return application.full_name if application else ""
