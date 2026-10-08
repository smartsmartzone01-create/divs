from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.identity.services.google_oidc import (
    GoogleAuthenticationNotConfigured,
    ensure_google_oidc_configured,
)


class GoogleReadinessView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            ensure_google_oidc_configured()
        except GoogleAuthenticationNotConfigured:
            return Response(
                {"provider": "google", "configured": False},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(
            {
                "provider": "google",
                "configured": True,
                "message": "Configuration exists; the OIDC flow still needs implementation and testing.",
            }
        )


class PhoneReadinessView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(
            {
                "provider": "phone",
                "configured": False,
                "message": "SMS/OTP delivery integration has not been added.",
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
