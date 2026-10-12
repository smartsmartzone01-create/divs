import hashlib

from rest_framework.throttling import SimpleRateThrottle


class InvitationCodeThrottle(SimpleRateThrottle):
    """Limit invitation-code checks by the email being checked."""

    scope = "invitation_code"

    def get_cache_key(self, request, view):
        email = (getattr(request, "data", {}).get("email") or "").strip().lower()
        ident = hashlib.sha256(email.encode("utf-8")).hexdigest() if email else self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
