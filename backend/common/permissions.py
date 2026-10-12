"""Shared role-based access policy for protected DIVS API views.

Views declare the profile required for an action; this module consistently
checks that the authenticated account has an active profile of that type.
Keep business-specific permissions in the relevant feature, but reuse this
policy instead of creating separate access rules for each profile.
"""

from rest_framework.permissions import BasePermission


PROFILE_MODELS = {
    "driver": ("apps.profiles.models", "DriverProfile"),
    "client": ("apps.profiles.models", "ClientProfile"),
    "operations": ("apps.profiles.models", "OperationsProfile"),
}


class HasRequiredProfile(BasePermission):
    """Allow access only when the account has the required active role profile.

    Set ``required_profile_type`` on a view to ``driver``, ``client``, or
    ``operations``. A missing or unsupported declaration fails closed.
    System superusers may enter operations-only views, but this does not grant
    driver or client access automatically.
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
