import hashlib

from rest_framework.throttling import SimpleRateThrottle, ScopedRateThrottle


class VerificationRequestThrottle(SimpleRateThrottle):
    """Limit code sends per normalized destination, regardless of entry point."""

    scope = "verification_request"

    def get_cache_key(self, request, view):
        data = getattr(request, "data", {})
        target = (data.get("email") or data.get("phone_number") or data.get("identifier") or "").strip().lower()
        if not target:
            return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}
        ident = hashlib.sha256(target.encode("utf-8")).hexdigest()
        return self.cache_format % {"scope": self.scope, "ident": ident}


class VerificationResendCooldownThrottle(SimpleRateThrottle):
    """Allow one verification request per destination per minute."""

    scope = "verification_resend"

    def get_cache_key(self, request, view):
        data = getattr(request, "data", {})
        target = (data.get("email") or data.get("phone_number") or data.get("identifier") or "").strip().lower()
        if not target:
            return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}
        ident = hashlib.sha256(target.encode("utf-8")).hexdigest()
        return self.cache_format % {"scope": self.scope, "ident": ident}


class AuthenticationAttemptThrottle(ScopedRateThrottle):
    """Shared baseline rate limit for password and verification endpoints."""

    scope = "login"
