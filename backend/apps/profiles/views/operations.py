from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from apps.profiles.models import OperationsProfile
from apps.profiles.serializers import OperationsProfileSerializer
from common.views import RoleProtectedAPIView


class OperationsProfileView(RoleProtectedAPIView):
    """Return only the signed-in member's operations profile."""

    required_profile_type = "operations"

    def get(self, request):
        profile = get_object_or_404(
            OperationsProfile.objects.select_related(
                "membership",
                "membership__account",
            ),
            membership__account=request.user,
        )
        return Response(OperationsProfileSerializer(profile).data)
