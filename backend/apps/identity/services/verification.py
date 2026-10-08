import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.utils import timezone

from apps.identity.models import VerificationCode


CODE_TTL_MINUTES = 10
MAX_CODE_ATTEMPTS = 5


class VerificationDeliveryNotConfigured(Exception):
    pass


def normalize_target(channel, target):
    value = target.strip()
    if channel == VerificationCode.Channel.EMAIL:
        return value.lower()
    return value


def issue_verification_code(channel, target, account=None):
    target = normalize_target(channel, target)
    raw_code = f"{secrets.randbelow(1_000_000):06d}"
    now = timezone.now()
    record = VerificationCode.objects.create(
        account=account,
        channel=channel,
        target=target,
        code_hash=make_password(raw_code),
        expires_at=now + timedelta(minutes=CODE_TTL_MINUTES),
    )

    if channel == VerificationCode.Channel.EMAIL:
        sent = send_mail(
            subject="Your DIVS verification code",
            message=f"Your DIVS verification code is {raw_code}. It expires in {CODE_TTL_MINUTES} minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[target],
            fail_silently=False,
        )
        if sent != 1:
            record.delete()
            raise VerificationDeliveryNotConfigured("Email delivery did not accept the message.")
    else:
        # Never pretend a phone code was sent without a configured SMS provider.
        record.delete()
        raise VerificationDeliveryNotConfigured("SMS/OTP delivery provider is not configured.")

    return record


def verify_code(channel, target, raw_code):
    target = normalize_target(channel, target)
    record = VerificationCode.objects.filter(
        channel=channel,
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
