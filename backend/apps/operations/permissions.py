from rest_framework.permissions import BasePermission

from apps.operations.models import OperationsMembership


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


def capabilities_for(user):
    """Return the explicit operations capabilities for an account."""
    if not user or not user.is_authenticated:
        return frozenset()

    # The system superuser is the initial authority and has the Admin policy.
    if user.is_superuser:
        return ROLE_CAPABILITIES[OperationsMembership.Role.ADMIN]

    membership = (
        OperationsMembership.objects.filter(account=user)
        .only("role")
        .first()
    )
    if membership is None:
        return frozenset()

    return ROLE_CAPABILITIES.get(membership.role, frozenset())


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
    """Only Admins and the initial system superuser can invite operations staff."""

    message = "Only an operations Admin can issue or revoke invitations."

    def has_permission(self, request, view):
        return "manage_invitations" in capabilities_for(request.user)


class SystemSuperuserOnly(BasePermission):
    """Keep approval of operations applications under the initial superuser."""

    message = "Only the system superuser can approve or reject operations applications."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_superuser)
