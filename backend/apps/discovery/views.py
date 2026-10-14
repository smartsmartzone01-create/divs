from django.db.models import Prefetch
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discovery.serializers import PublicDriverSerializer
from apps.performance.models import AvailabilityRestriction, DriverScore
from apps.profiles.models import DriverProfile
from apps.verification.models import DriverVerificationCheck


class PublicDriverDiscoveryView(APIView):
    """Public search for eligible drivers without exposing private contact details."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        params = request.query_params
        min_score = self._parse_score(params.get("min_score"), "min_score")
        max_score = self._parse_score(params.get("max_score"), "max_score")
        if isinstance(min_score, Response):
            return min_score
        if isinstance(max_score, Response):
            return max_score
        if min_score is not None and max_score is not None and min_score > max_score:
            return Response({"detail": "min_score cannot exceed max_score."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            limit = int(params.get("limit", 25))
        except (TypeError, ValueError):
            return Response({"detail": "limit must be an integer."}, status=status.HTTP_400_BAD_REQUEST)
        if limit < 1 or limit > 100:
            return Response({"detail": "limit must be between 1 and 100."}, status=status.HTTP_400_BAD_REQUEST)

        profiles = (
            DriverProfile.objects.filter(
                status=DriverProfile.Status.ACTIVE,
                verification__status="approved",
            )
            .select_related("registration", "verification", "performance_score")
            .prefetch_related(
                "verification__checks__verified_licence_classes",
                Prefetch(
                    "availability_restrictions",
                    queryset=AvailabilityRestriction.objects.filter(status=AvailabilityRestriction.Status.ACTIVE),
                    to_attr="active_performance_restrictions",
                ),
            )
        )
        eligible = []
        requested_class = params.get("licence_class", "").strip().upper()
        for profile in profiles:
            if not profile.verification.is_discoverable:
                continue
            if getattr(profile, "active_performance_restrictions", []):
                continue
            registration = profile.registration
            if params.get("region") and params["region"].casefold() not in registration.region.casefold():
                continue
            if params.get("district") and params["district"].casefold() not in registration.district.casefold():
                continue
            if params.get("residential_area") and params["residential_area"].casefold() not in registration.residential_area.casefold():
                continue
            if params.get("experience") and params["experience"] != registration.driving_experience:
                continue

            # Use the prefetched relations instead of issuing per-driver queries.
            checks = list(profile.verification.checks.all())
            licence_check = next(
                (
                    check for check in checks
                    if check.check_type == DriverVerificationCheck.CheckType.DRIVING_LICENCE
                    and check.status == DriverVerificationCheck.Status.PASSED
                    and check.result_code == DriverVerificationCheck.ResultCode.VALID
                ),
                None,
            )
            classes = [] if licence_check is None else sorted(
                licence_class.licence_class
                for licence_class in licence_check.verified_licence_classes.all()
                if licence_class.is_current
            )
            if requested_class and requested_class not in classes:
                continue

            try:
                score = profile.performance_score.effective_score
            except DriverScore.DoesNotExist:
                score = None
            # The public hiring directory must enforce the threshold even if a
            # restriction record is missing or has not yet been created.
            if score is not None and score < 40:
                continue
            if min_score is not None and (score is None or score < min_score):
                continue
            if max_score is not None and (score is None or score > max_score):
                continue
            eligible.append((profile, score))

        eligible.sort(
            key=lambda item: (
                item[1] is not None,
                item[1] if item[1] is not None else -1,
                item[0].updated_at,
            ),
            reverse=True,
        )
        total = len(eligible)
        page = [profile for profile, _score in eligible[:limit]]
        return Response({"count": total, "results": PublicDriverSerializer(page, many=True).data})

    @staticmethod
    def _parse_score(raw_value, field_name):
        if raw_value in (None, ""):
            return None
        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            return Response({"detail": f"{field_name} must be an integer from 0 to 100."}, status=status.HTTP_400_BAD_REQUEST)
        if not 0 <= value <= 100:
            return Response({"detail": f"{field_name} must be between 0 and 100."}, status=status.HTTP_400_BAD_REQUEST)
        return value
