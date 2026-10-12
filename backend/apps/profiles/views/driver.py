from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from apps.profiles.models import DriverProfile
from apps.profiles.serializers import DriverProfileSerializer
from common.views import RoleProtectedAPIView


class DriverProfileView(RoleProtectedAPIView):
    """Return the signed-in driver's own profile and registration information."""

    required_profile_type = "driver"

    def get(self, request):
        profile = get_object_or_404(
            DriverProfile.objects.select_related("registration", "registration__account"),
            registration__account=request.user,
        )
        return Response(DriverProfileSerializer(profile).data)
