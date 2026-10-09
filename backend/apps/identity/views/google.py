from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from django.conf import settings

from apps.identity.models import Account, ExternalIdentity
from apps.identity.services.sessions import create_auth_session


class GoogleSignInView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        credential = request.data.get("credential")
        if not isinstance(credential, str) or not credential:
            return Response(
                {"detail": "A Google credential is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not settings.GOOGLE_OIDC_CLIENT_ID:
            return Response(
                {"detail": "Google sign-in is not configured yet."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            claims = id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                settings.GOOGLE_OIDC_CLIENT_ID,
            )
        except Exception:
            # Never trust claims from a token that failed Google's signature/audience checks.
            return Response(
                {"detail": "Google sign-in could not be verified."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        subject = claims.get("sub")
        email = (claims.get("email") or "").strip().lower()
        email_verified = claims.get("email_verified") is True
        if not subject or not email or not email_verified:
            return Response(
                {"detail": "Google must provide a verified email identity."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        external = ExternalIdentity.objects.select_related("account").filter(
            provider=ExternalIdentity.Provider.GOOGLE,
            subject=subject,
        ).first()
        if external is None:
            # Never merge accounts automatically based only on matching email addresses.
            return Response(
                {
                    "detail": "This Google identity is not linked to a DIVS account. Registration or authenticated account linking is required.",
                    "registration_required": True,
                },
                status=status.HTTP_409_CONFLICT,
            )
        if not external.account.is_active:
            raise AuthenticationFailed("This account is inactive.")

        tokens = create_auth_session(external.account, request)
        return Response(tokens, status=status.HTTP_200_OK)
