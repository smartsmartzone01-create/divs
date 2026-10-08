from django.conf import settings


class GoogleAuthenticationNotConfigured(Exception):
    """Raised when Google OIDC credentials or callback settings are missing."""


def ensure_google_oidc_configured():
    """Validate configuration before a Google OIDC flow is started.

    The authorization-code flow, state/nonce validation, token exchange, and ID
    token verification must be implemented together before enabling sign-in.
    This foundation intentionally does not pretend Google login is operational
    without those security checks and real provider credentials.
    """
    required = (
        settings.GOOGLE_OIDC_CLIENT_ID,
        settings.GOOGLE_OIDC_CLIENT_SECRET,
        settings.GOOGLE_OIDC_REDIRECT_URI,
    )
    if not all(required):
        raise GoogleAuthenticationNotConfigured(
            "Google sign-in is not configured yet."
        )
