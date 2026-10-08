class PhoneAuthenticationNotConfigured(Exception):
    """Raised until an SMS/OTP provider is selected and configured."""


def request_phone_verification(phone_number):
    """Extension point for a future OTP provider.

    Do not mark a phone number verified until a real OTP has been delivered and
    successfully checked. Provider integration will be added after local setup.
    """
    raise PhoneAuthenticationNotConfigured(
        "Phone verification is not configured yet."
    )


def verify_phone_code(phone_number, code):
    """Extension point for validating a provider-issued one-time code."""
    raise PhoneAuthenticationNotConfigured(
        "Phone verification is not configured yet."
    )
