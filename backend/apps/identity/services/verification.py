import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from apps.identity.models import VerificationCode
from apps.identity.services.phone_auth import (
    PhoneAuthenticationNotConfigured,
    request_phone_verification,
)


CODE_TTL_MINUTES = 10
MAX_CODE_ATTEMPTS = 5


class VerificationDeliveryNotConfigured(Exception):
    pass


def normalize_target(channel, target):
    value = target.strip()
    if channel == VerificationCode.Channel.EMAIL:
        return value.lower()
    return value


def issue_verification_code(
    channel,
    target,
    account=None,
    purpose=VerificationCode.Purpose.IDENTITY_VERIFICATION,
):
    target = normalize_target(channel, target)
    raw_code = f"{secrets.randbelow(1_000_000):06d}"
    now = timezone.now()
    record = VerificationCode.objects.create(
        account=account,
        channel=channel,
        purpose=purpose,
        target=target,
        code_hash=make_password(raw_code),
        expires_at=now + timedelta(minutes=CODE_TTL_MINUTES),
    )

    if channel == VerificationCode.Channel.EMAIL:
        try:
            sent = send_mail(
                subject=(
                    "Reset your DIVS password"
                    if purpose == VerificationCode.Purpose.PASSWORD_RESET
                    else "Your DIVS verification code"
                ),
                message=(
                    f"Your DIVS password reset code is {raw_code}. "
                    f"It expires in {CODE_TTL_MINUTES} minutes."
                    if purpose == VerificationCode.Purpose.PASSWORD_RESET
                    else f"Your DIVS verification code is {raw_code}. "
                    f"It expires in {CODE_TTL_MINUTES} minutes."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[target],
                fail_silently=False,
            )
        except Exception:
            record.delete()
            raise
        if sent != 1:
            record.delete()
            raise VerificationDeliveryNotConfigured("Email delivery did not accept the message.")
    elif channel == VerificationCode.Channel.PHONE:
        try:
            request_phone_verification(
                target,
                raw_code,
                expires_in_seconds=CODE_TTL_MINUTES * 60,
            )
        except PhoneAuthenticationNotConfigured as exc:
            record.delete()
            raise VerificationDeliveryNotConfigured(str(exc)) from exc
        except Exception:
            record.delete()
            raise
    else:
        record.delete()
        raise VerificationDeliveryNotConfigured("Unsupported verification channel.")

    return record


@transaction.atomic
def verify_code(
    channel,
    target,
    raw_code,
    purpose=VerificationCode.Purpose.IDENTITY_VERIFICATION,
):
    target = normalize_target(channel, target)
    record = VerificationCode.objects.select_for_update().filter(
        channel=channel,
        purpose=purpose,
        target=target,
        consumed_at__isnull=True,
    ).order_by("-created_at").first()

    if record is None or not record.is_usable:
        return False
    record.attempts += 1
    if check_password(raw_code, record.code_hash):
        record.consumed_at = timezone.now()
        record.save(update_fields=["attempts", "consumed_at"])
        return True
    record.save(update_fields=["attempts"])
    return False
