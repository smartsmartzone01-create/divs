from rest_framework.permissions import BasePermission


class CanIssueOperationsInvitations(BasePermission):
    """Only the system superuser can issue invitations until approved admin roles exist."""

    message = "Only an authorized system administrator can issue operations invitations."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_superuser)
