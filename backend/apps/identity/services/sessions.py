from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.identity.models import AuthSession


def create_auth_session(account, request):
    meta = getattr(request, "META", {}) if request is not None else {}
    forwarded_for = meta.get("HTTP_X_FORWARDED_FOR", "")
    remote_ip = forwarded_for.split(",")[0].strip() if forwarded_for else meta.get("REMOTE_ADDR")
    try:
        # Only accept a valid IP literal; proxy trust must be configured at deployment.
        import ipaddress
        remote_ip = str(ipaddress.ip_address(remote_ip)) if remote_ip else None
    except ValueError:
        remote_ip = None

    user_agent = meta.get("HTTP_USER_AGENT", "")[:512]
    device_label = user_agent[:120]
    lifetime = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]
    session = AuthSession.objects.create(
        account=account,
        device_label=device_label,
        user_agent=user_agent,
        ip_address=remote_ip,
        expires_at=timezone.now() + lifetime,
    )
    refresh = RefreshToken.for_user(account)
    refresh["sid"] = str(session.id)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "session_id": str(session.id),
    }
