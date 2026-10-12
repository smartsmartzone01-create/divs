"""Shared role-based access policy for protected DIVS API views.

Views declare the profile required for an action; this module consistently
checks that the authenticated account has an active profile of that type.
Keep business-specific permissions in the relevant feature, but reuse this
policy instead of creating separate access rules for each profile.
"""

from rest_framework.permissions import BasePermission

from apps.operations.models import OperationsMembership


PROFILE_MODELS = {
    "driver": ("apps.profiles.models", "DriverProfile"),
    "client": ("apps.profiles.models", "ClientProfile"),
    "operations": ("apps.profiles.models", "OperationsProfile"),
}


class HasRequiredProfile(BasePermission):
    """Allow access only when the account has the required active role profile.

    The initial system superuser may enter operations-only views without an
    operations profile. Approved Admins are also Django superusers, but their
    operations profile must remain active like any other member's profile.
    """

    message = "Your account does not have an active profile for this area."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        profile_type = getattr(view, "required_profile_type", None)
        if profile_type not in PROFILE_MODELS:
            return False

        if profile_type == "operations" and user.is_superuser:
            # Only the initial system superuser has no approved membership.
            # An approved Admin has a membership and must pass the normal
            # active-profile check so suspension can revoke access.
            if not OperationsMembership.objects.filter(account=user).exists():
                return True

        module_path, model_name = PROFILE_MODELS[profile_type]
        module = __import__(module_path, fromlist=[model_name])
        profile_model = getattr(module, model_name)
        return profile_model.objects.filter(
            **{f"{self._relationship_field(profile_type)}__account": user},
            status="active",
        ).exists()

    @staticmethod
    def _relationship_field(profile_type):
        if profile_type in {"driver", "client"}:
            return "registration"
        return "membership"
