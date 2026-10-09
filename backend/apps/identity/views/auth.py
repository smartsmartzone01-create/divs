from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.identity.serializers import AccountSerializer


class CurrentAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(AccountSerializer(request.user).data)
