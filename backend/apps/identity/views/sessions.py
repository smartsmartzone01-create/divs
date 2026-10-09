from django.utils import timezone
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.identity.models import AuthSession


class AuthSessionSerializer(serializers.ModelSerializer):
    current = serializers.SerializerMethodField()

    class Meta:
        model = AuthSession
        fields = ("id", "device_label", "ip_address", "created_at", "last_seen_at", "expires_at", "revoked_at", "current")
        read_only_fields = fields

    def get_current(self, obj):
        request = self.context.get("request")
        return bool(request and request.auth and str(request.auth.get("sid")) == str(obj.id))


class SessionListView(generics.ListAPIView):
    serializer_class = AuthSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AuthSession.objects.filter(account=self.request.user)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        session_id = request.auth.get("sid") if request.auth else None
        if session_id:
            AuthSession.objects.filter(
                id=session_id,
                account=request.user,
                revoked_at__isnull=True,
            ).update(revoked_at=timezone.now())
        return Response(status=status.HTTP_204_NO_CONTENT)


class RevokeSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, session_id):
        updated = AuthSession.objects.filter(
            id=session_id,
            account=request.user,
            revoked_at__isnull=True,
        ).update(revoked_at=timezone.now())
        if not updated:
            return Response({"detail": "Session not found or already revoked."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
