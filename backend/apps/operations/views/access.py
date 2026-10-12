from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.operations.models import OperationsMembership
from apps.operations.permissions import (
    ROLE_CAPABILITIES,
    IsOperationsWorkspaceMember,
    capabilities_for,
)


class OperationsMyAccessView(APIView):
    """Return the caller's approved operations role and its explicit capabilities."""

    permission_classes = [IsAuthenticated, IsOperationsWorkspaceMember]

    def get(self, request):
        capabilities = sorted(capabilities_for(request.user))
        if request.user.is_superuser:
            role = OperationsMembership.Role.ADMIN
        else:
            role = request.user.operations_membership.role

        return Response(
            {
                "role": role,
                "capabilities": capabilities,
                "note": (
                    "Capabilities describe the authorization policy. A capability "
                    "does not mean its business workflow endpoint has already been implemented."
                ),
            }
        )
