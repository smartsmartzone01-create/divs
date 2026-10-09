from rest_framework_simplejwt.views import TokenObtainPairView

from apps.identity.serializers import SharedTokenObtainPairSerializer
from common.throttles.authentication import AuthenticationAttemptThrottle, LoginIdentifierThrottle


class SharedTokenObtainPairView(TokenObtainPairView):
    throttle_scope = "login"
    serializer_class = SharedTokenObtainPairSerializer
    throttle_classes = [AuthenticationAttemptThrottle, LoginIdentifierThrottle]
