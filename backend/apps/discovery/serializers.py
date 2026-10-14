from rest_framework import serializers

from apps.performance.models import DriverScore
from apps.profiles.models import DriverProfile
from apps.verification.models import DriverVerificationCheck


class PublicDriverSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    region = serializers.CharField(source="registration.region", read_only=True)
    district = serializers.CharField(source="registration.district", read_only=True)
    residential_area = serializers.CharField(source="registration.residential_area", read_only=True)
    driving_experience = serializers.CharField(source="registration.driving_experience", read_only=True)
    verified_licence_classes = serializers.SerializerMethodField()
    performance_score = serializers.SerializerMethodField()
    availability = serializers.SerializerMethodField()

    class Meta:
        model = DriverProfile
        fields = [
            "id", "display_name", "region", "district", "residential_area",
            "driving_experience", "verified_licence_classes", "performance_score",
            "availability",
        ]
        read_only_fields = fields

    def get_display_name(self, obj):
        registration = obj.registration
        return f"{registration.first_name} {registration.last_name}".strip()

    def get_verified_licence_classes(self, obj):
        check = obj.verification.checks.filter(
            check_type=DriverVerificationCheck.CheckType.DRIVING_LICENCE,
            status=DriverVerificationCheck.Status.PASSED,
            result_code=DriverVerificationCheck.ResultCode.VALID,
        ).first()
        if check is None:
            return []
        return list(
            check.verified_licence_classes.filter(is_current=True)
            .order_by("licence_class")
            .values_list("licence_class", flat=True)
        )

    def get_performance_score(self, obj):
        try:
            return obj.performance_score.effective_score
        except DriverScore.DoesNotExist:
            return None

    def get_availability(self, obj):
        return "available"
