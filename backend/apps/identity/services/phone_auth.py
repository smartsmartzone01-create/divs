from django.conf import settings
from django.utils.module_loading import import_string


class PhoneAuthenticationNotConfigured(Exception):
    """Raised when no SMS delivery adapter has been configured."""


def get_sms_provider():
    provider_path = getattr(settings, "SMS_OTP_PROVIDER_CLASS", "")
    if not provider_path:
        raise PhoneAuthenticationNotConfigured(
            "SMS/OTP delivery provider is not configured."
        )
    try:
        provider_class = import_string(provider_path)
    except (ImportError, AttributeError) as exc:
        raise PhoneAuthenticationNotConfigured(
            "The configured SMS/OTP provider could not be loaded."
        ) from exc
    return provider_class()


def request_phone_verification(phone_number, code, expires_in_seconds):
    """Deliver a DIVS-generated OTP through the configured provider adapter.

    The adapter class must implement:
        send_verification_code(phone_number, code, expires_in_seconds=...)
    It must raise an exception when delivery fails. It must never log the OTP.
    """
    provider = get_sms_provider()
    provider.send_verification_code(
        phone_number,
        code,
        expires_in_seconds=expires_in_seconds,
    )


def verify_phone_code(phone_number, code):
    """Phone codes are verified by DIVS against their hashed, purpose-scoped record."""
    # The code is intentionally not delegated to an SMS provider: delivery and
    # verification share DIVS's hashed code, expiry, and attempt-limit controls.
    from apps.identity.models import VerificationCode
    from apps.identity.services.verification import verify_code

    return verify_code(VerificationCode.Channel.PHONE, phone_number, code)
