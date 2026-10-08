import hashlib

from rest_framework.throttling import ScopedRateThrottle, SimpleRateThrottle


class VerificationRequestThrottle(SimpleRateThrottle):
    """Limit verification-code sends per normalized destination."""

    scope = "verification_request"

    def get_cache_key(self, request, view):
        data = getattr(request, "data", {})
        target = (data.get("email") or data.get("phone_number") or data.get("identifier") or "").strip().lower()
        ident = hashlib.sha256(target.encode("utf-8")).hexdigest() if target else self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class VerificationResendCooldownThrottle(SimpleRateThrottle):
    """Allow one verification request per destination per minute."""

    scope = "verification_resend"

    def get_cache_key(self, request, view):
        data = getattr(request, "data", {})
        target = (data.get("email") or data.get("phone_number") or data.get("identifier") or "").strip().lower()
        ident = hashlib.sha256(target.encode("utf-8")).hexdigest() if target else self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class AuthenticationAttemptThrottle(ScopedRateThrottle):
    """Shared baseline rate limit for authentication attempts."""

    scope = "login"


class VerificationConfirmThrottle(ScopedRateThrottle):
    """Baseline IP-based limit in addition to per-code attempt limits."""

    scope = "verification_confirm"
