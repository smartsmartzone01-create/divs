from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.identity.serializers import AccountRegistrationSerializer, AccountSerializer


class RegistrationView(generics.CreateAPIView):
    serializer_class = AccountRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = serializer.save()
        return Response(
            {
                "account": AccountSerializer(account).data,
                "message": "Account created. Email verification is not configured yet.",
            },
            status=status.HTTP_201_CREATED,
        )


class CurrentAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(AccountSerializer(request.user).data)
