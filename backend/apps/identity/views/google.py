from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework import permissions, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import AuthenticationFailed as JWTAuthenticationFailed

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from apps.identity.models import ExternalIdentity
from apps.identity.services.sessions import create_auth_session


Account = get_user_model()


def verified_google_claims(credential):
    """Validate the Google ID token and return only the claims DIVS needs."""
    if not isinstance(credential, str) or not credential:
        raise ValueError("A Google credential is required.")
    if not settings.GOOGLE_OIDC_CLIENT_ID:
        raise RuntimeError("Google sign-in is not configured yet.")

    claims = id_token.verify_oauth2_token(
        credential,
        google_requests.Request(),
        settings.GOOGLE_OIDC_CLIENT_ID,
    )
    subject = claims.get("sub")
    email = (claims.get("email") or "").strip().lower()
    if not subject or not email or claims.get("email_verified") is not True:
        raise ValueError("Google must provide a verified email identity.")
    return subject, email


class GoogleSignInView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        credential = request.data.get("credential")
        try:
            subject, email = verified_google_claims(credential)
        except RuntimeError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception:
            # Do not trust claims from a token that failed signature/audience checks.
            return Response(
                {"detail": "Google sign-in could not be verified."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        external = ExternalIdentity.objects.select_related("account").filter(
            provider=ExternalIdentity.Provider.GOOGLE,
            subject=subject,
        ).first()
        if external is not None:
            if not external.account.is_active:
                raise AuthenticationFailed("This account is inactive.")
            return Response(create_auth_session(external.account, request), status=status.HTTP_200_OK)

        # A verified Google email may create a bare identity account. DIVS registration
        # remains responsible for choosing driver/client; identity does not choose a role.
        # Never merge an existing password account merely because its email matches.
        if request.user and request.user.is_authenticated:
            account = request.user
        else:
            existing_account = Account.objects.filter(email__iexact=email).first()
            if existing_account is not None:
                return Response(
                    {
                        "detail": "An account already uses this email. Sign in to that account first, then link Google from an authenticated session.",
                        "account_linking_required": True,
                    },
                    status=status.HTTP_409_CONFLICT,
                )
            account = None

        try:
            with transaction.atomic():
                if account is None:
                    account = Account.objects.create_user(
                        email=email,
                        password=None,
                        email_verified=True,
                    )
                ExternalIdentity.objects.create(
                    account=account,
                    provider=ExternalIdentity.Provider.GOOGLE,
                    subject=subject,
                    provider_email=email,
                )
        except IntegrityError:
            # A concurrent first sign-in may have created the provider link already.
            external = ExternalIdentity.objects.select_related("account").filter(
                provider=ExternalIdentity.Provider.GOOGLE,
                subject=subject,
            ).first()
            if external is None:
                return Response(
                    {"detail": "This Google identity could not be linked safely. Please retry."},
                    status=status.HTTP_409_CONFLICT,
                )
            account = external.account

        if not account.is_active:
            raise AuthenticationFailed("This account is inactive.")
        return Response(create_auth_session(account, request), status=status.HTTP_200_OK)
