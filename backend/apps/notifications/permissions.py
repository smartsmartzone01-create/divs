from rest_framework.permissions import BasePermission

from apps.operations.models import OperationsApplication, OperationsMembership
from apps.profiles.models import OperationsProfile


class OperationsNotificationAccess(BasePermission):
    """Allow active operations members or applicants to see their own stream."""

    message = "An operations application or active operations profile is required."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        if OperationsProfile.objects.filter(
            membership__account=user,
            status="active",
        ).exists():
            return True
        if user.is_superuser and not OperationsMembership.objects.filter(account=user).exists():
            return True
        return OperationsApplication.objects.filter(account=user).exists()
