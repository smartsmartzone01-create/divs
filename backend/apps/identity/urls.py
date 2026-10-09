from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.identity.serializers.tokens import TrackedTokenRefreshSerializer
from apps.identity.views.auth import CurrentAccountView
from apps.identity.views.google import GoogleSignInView
from apps.identity.views.providers import GoogleReadinessView, PhoneReadinessView
from apps.identity.views.sessions import LogoutView, RevokeSessionView, SessionListView
from apps.identity.views.tokens import SharedTokenObtainPairView
from apps.identity.views.verification import VerificationConfirmView, VerificationRequestView

app_name = "identity"

urlpatterns = [
    path("token/", SharedTokenObtainPairView.as_view(), name="token"),
    path(
        "token/refresh/",
        TokenRefreshView.as_view(serializer_class=TrackedTokenRefreshSerializer),
        name="token-refresh",
    ),
    path("me/", CurrentAccountView.as_view(), name="me"),
    path("sessions/", SessionListView.as_view(), name="sessions"),
    path("sessions/<uuid:session_id>/", RevokeSessionView.as_view(), name="revoke-session"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("verification/request/", VerificationRequestView.as_view(), name="verification-request"),
    path("verification/confirm/", VerificationConfirmView.as_view(), name="verification-confirm"),
    path("providers/google/", GoogleReadinessView.as_view(), name="google-readiness"),
    path("providers/google/sign-in/", GoogleSignInView.as_view(), name="google-sign-in"),
    path("providers/phone/", PhoneReadinessView.as_view(), name="phone-readiness"),
]
