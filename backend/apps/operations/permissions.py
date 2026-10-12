from rest_framework.permissions import BasePermission

from apps.operations.models import OperationsMembership
from apps.profiles.models import OperationsProfile


# This is the authorization policy for operations actions. Do not grant a
# capability merely because an account is authenticated.
ROLE_CAPABILITIES = {
    OperationsMembership.Role.ADMIN: frozenset(
        {
            "view_operations_workspace",
            "manage_driver_registrations",
            "review_driver_verification",
            "manage_driver_performance",
            "manage_invitations",
        }
    ),
    OperationsMembership.Role.OPERATOR: frozenset(
        {
            "view_operations_workspace",
            "manage_driver_registrations",
            "review_driver_verification",
            "manage_driver_performance",
        }
    ),
}


def is_initial_system_superuser(user):
    """Only the earliest superuser without an operations membership is system root."""
    if not user or not user.is_authenticated or not user.is_superuser:
        return False
    first_root = (
        user.__class__.objects.filter(
            is_superuser=True,
            operations_membership__isnull=True,
        )
        .order_by("date_joined")
        .first()
    )
    return first_root is not None and first_root.pk == user.pk


def capabilities_for(user):
    """Return capabilities only for the initial superuser or an active member."""
    if not user or not user.is_authenticated:
        return frozenset()

    membership = OperationsMembership.objects.filter(account=user).only("role").first()
    if membership is not None:
        if not OperationsProfile.objects.filter(
            membership=membership,
            status=OperationsProfile.Status.ACTIVE,
        ).exists():
            return frozenset()
        return ROLE_CAPABILITIES.get(membership.role, frozenset())

    if is_initial_system_superuser(user):
        return ROLE_CAPABILITIES[OperationsMembership.Role.ADMIN]

    return frozenset()


class HasOperationsCapability(BasePermission):
    """Base permission for views that declare a required capability."""

    message = "Your operations role does not allow this action."

    def has_permission(self, request, view):
        required = getattr(view, "required_operations_capability", None)
        return bool(required and required in capabilities_for(request.user))


class IsOperationsWorkspaceMember(BasePermission):
    message = "An approved operations membership is required."

    def has_permission(self, request, view):
        return "view_operations_workspace" in capabilities_for(request.user)


class CanIssueOperationsInvitations(BasePermission):
    """Only active Admins and the initial system superuser can manage invitations."""

    message = "Only an operations Admin can issue or revoke invitations."

    def has_permission(self, request, view):
        return "manage_invitations" in capabilities_for(request.user)


class SystemSuperuserOnly(BasePermission):
    """Keep approval of operations applications under the initial superuser."""

    message = "Only the system superuser can approve or reject operations applications."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not user.is_superuser:
            return False
        # Approved Admins are marked is_superuser for broad privileges, but
        # must not approve further operations applications themselves.
        return is_initial_system_superuser(user)
