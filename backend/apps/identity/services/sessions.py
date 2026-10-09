from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.identity.models import AuthSession


def create_auth_session(account, request):
    meta = getattr(request, "META", {}) if request is not None else {}
    remote_ip = meta.get("REMOTE_ADDR")
    user_agent = meta.get("HTTP_USER_AGENT", "")[:512]
    try:
        import ipaddress
        remote_ip = str(ipaddress.ip_address(remote_ip)) if remote_ip else None
    except ValueError:
        remote_ip = None

    session = AuthSession.objects.create(
        account=account,
        device_label=user_agent[:120],
        user_agent=user_agent,
        ip_address=remote_ip,
        expires_at=timezone.now() + settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
    )
    refresh = RefreshToken.for_user(account)
    refresh["sid"] = str(session.id)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "session_id": str(session.id),
    }
