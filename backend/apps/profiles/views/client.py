from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from apps.profiles.models import ClientProfile
from apps.profiles.serializers import ClientProfileSerializer
from common.views import RoleProtectedAPIView


class ClientProfileView(RoleProtectedAPIView):
    """Return only the signed-in client's own profile and registration."""

    required_profile_type = "client"

    def get(self, request):
        profile = get_object_or_404(
            ClientProfile.objects.select_related(
                "registration",
                "registration__account",
            ),
            registration__account=request.user,
        )
        return Response(ClientProfileSerializer(profile).data)
