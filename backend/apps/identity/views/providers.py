from django.conf import settings
from django.utils.module_loading import import_string
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
                "message": "Google ID-token validation is configured. Identity sign-in does not select a driver or client role.",
            }
        )


class PhoneReadinessView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        provider_path = getattr(settings, "SMS_OTP_PROVIDER_CLASS", "")
        if not provider_path:
            return Response(
                {
                    "provider": "phone",
                    "configured": False,
                    "message": "An SMS/OTP delivery adapter is not configured.",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        try:
            provider_class = import_string(provider_path)
            if not callable(provider_class) or not hasattr(provider_class, "send_verification_code"):
                raise AttributeError("SMS adapter must implement send_verification_code.")
        except (ImportError, AttributeError):
            return Response(
                {
                    "provider": "phone",
                    "configured": False,
                    "message": "The configured SMS/OTP delivery adapter could not be loaded.",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(
            {
                "provider": "phone",
                "configured": True,
                "message": "An SMS/OTP adapter is configured. Verify delivery with provider test credentials before production use.",
            }
        )
