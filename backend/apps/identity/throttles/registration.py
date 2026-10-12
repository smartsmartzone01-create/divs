import hashlib

from rest_framework.throttling import SimpleRateThrottle


class AccountRegistrationThrottle(SimpleRateThrottle):
    """Limit creation of shared identity accounts by client IP."""

    scope = "account_registration"

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        digest = hashlib.sha256(ident.encode("utf-8")).hexdigest()
        return self.cache_format % {"scope": self.scope, "ident": digest}
