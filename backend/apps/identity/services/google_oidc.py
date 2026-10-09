from django.conf import settings


class GoogleAuthenticationNotConfigured(Exception):
    """Raised when Google ID-token verification has no configured client ID."""


def ensure_google_oidc_configured():
    if not settings.GOOGLE_OIDC_CLIENT_ID:
        raise GoogleAuthenticationNotConfigured(
            "Google sign-in is not configured yet."
        )
