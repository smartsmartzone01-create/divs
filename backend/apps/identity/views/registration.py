from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.identity.serializers import AccountRegistrationSerializer, AccountSerializer
from apps.identity.throttles.registration import AccountRegistrationThrottle


class AccountRegistrationView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AccountRegistrationThrottle]

    def post(self, request):
        serializer = AccountRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = serializer.save()
        return Response(AccountSerializer(account).data, status=status.HTTP_201_CREATED)
