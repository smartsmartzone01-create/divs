from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.identity.views.auth import CurrentAccountView, RegistrationView
from apps.identity.views.providers import GoogleReadinessView, PhoneReadinessView

app_name = "identity"

urlpatterns = [
    path("register/", RegistrationView.as_view(), name="register"),
    path("token/", TokenObtainPairView.as_view(), name="token"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", CurrentAccountView.as_view(), name="me"),
    path("providers/google/", GoogleReadinessView.as_view(), name="google-readiness"),
    path("providers/phone/", PhoneReadinessView.as_view(), name="phone-readiness"),
]
