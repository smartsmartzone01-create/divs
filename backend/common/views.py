from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from common.permissions import HasRequiredProfile


class RoleProtectedAPIView(APIView):
    """Base API view for endpoints limited to one active role profile.

    Subclasses must set ``required_profile_type`` to ``driver``, ``client``,
    or ``operations``. Registration endpoints should not inherit this class,
    because people need to register before they have a profile.
    """

    permission_classes = [IsAuthenticated, HasRequiredProfile]
    required_profile_type = None
