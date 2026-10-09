from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer

from apps.identity.models import AuthSession
from apps.identity.services.sessions import create_auth_session


class SharedTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "identifier"

    def validate(self, attrs):
        identifier = attrs.get(self.username_field, "")
        if isinstance(identifier, str):
            attrs[self.username_field] = identifier.strip()
        super().validate(attrs)
        request = self.context.get("request")
        return create_auth_session(self.user, request)


class TrackedTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

        try:
            refresh = RefreshToken(attrs["refresh"])
            session_id = refresh.get("sid")
            if not session_id:
                raise InvalidToken("This token is not associated with an active session.")
            session = AuthSession.objects.filter(
                id=session_id,
                account_id=refresh.get("user_id"),
                revoked_at__isnull=True,
                expires_at__gt=__import__("django.utils.timezone", fromlist=["now"]).now(),
            ).first()
            if session is None:
                raise InvalidToken("This session has expired or been revoked.")
        except (TokenError, ValueError) as exc:
            raise InvalidToken("Refresh token is invalid.") from exc
        return super().validate(attrs)
