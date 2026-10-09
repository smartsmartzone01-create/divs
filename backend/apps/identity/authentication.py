from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.identity.models import AuthSession


class SessionJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None
        user, token = result
        session_id = token.get("sid")
        if not session_id:
            raise AuthenticationFailed("This token is not associated with an active session.")
        session = AuthSession.objects.filter(
            id=session_id,
            account=user,
            revoked_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).first()
        if session is None:
            raise AuthenticationFailed("This session has expired or been revoked.")
        AuthSession.objects.filter(id=session.id).update(last_seen_at=timezone.now())
        return user, token
