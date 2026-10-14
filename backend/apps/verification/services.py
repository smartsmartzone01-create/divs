from django.db import transaction
from django.utils import timezone

from apps.notifications.models import Notification
from apps.notifications.services import create_notification
from apps.verification.models import (
    DriverVerification,
    DriverVerificationCheck,
    VerifiedDriverLicenceClass,
)


class VerificationReviewError(Exception):
    """Raised when a verification check cannot be reviewed as requested."""


@transaction.atomic
def review_driver_check(
    *,
    check_id,
    reviewer,
    status,
    method=DriverVerificationCheck.Method.MANUAL,
    result_code="",
):
    """Record a minimal outcome and notify the driver if their overall status changes."""
    allowed_statuses = {
        DriverVerificationCheck.Status.PASSED,
        DriverVerificationCheck.Status.FAILED,
        DriverVerificationCheck.Status.NEEDS_REVIEW,
        DriverVerificationCheck.Status.UNAVAILABLE,
    }
    if status not in allowed_statuses:
        raise VerificationReviewError("Unsupported verification outcome.")
    if method not in DriverVerificationCheck.Method.values:
        raise VerificationReviewError("Unsupported verification method.")
    if result_code and result_code not in DriverVerificationCheck.ResultCode.values:
        raise VerificationReviewError("Unsupported result code.")

    compatible_results = {
        DriverVerificationCheck.CheckType.NATIONAL_IDENTITY: {
            DriverVerificationCheck.ResultCode.MATCH,
            DriverVerificationCheck.ResultCode.MISMATCH,
            DriverVerificationCheck.ResultCode.INCONCLUSIVE,
        },
        DriverVerificationCheck.CheckType.DRIVING_LICENCE: {
            DriverVerificationCheck.ResultCode.VALID,
            DriverVerificationCheck.ResultCode.INVALID,
            DriverVerificationCheck.ResultCode.INCONCLUSIVE,
        },
        DriverVerificationCheck.CheckType.TRAFFIC_RECORDS: {
            DriverVerificationCheck.ResultCode.CLEAR,
            DriverVerificationCheck.ResultCode.RECORD_FOUND,
            DriverVerificationCheck.ResultCode.INCONCLUSIVE,
        },
        DriverVerificationCheck.CheckType.ACCIDENT_RECORDS: {
            DriverVerificationCheck.ResultCode.CLEAR,
            DriverVerificationCheck.ResultCode.RECORD_FOUND,
            DriverVerificationCheck.ResultCode.INCONCLUSIVE,
        },
    }

    check = (
        DriverVerificationCheck.objects.select_for_update()
        .select_related("verification", "verification__profile", "verification__profile__registration")
        .filter(pk=check_id)
        .first()
    )
    if check is None:
        raise VerificationReviewError("Verification check not found.")
    if result_code and result_code not in compatible_results[check.check_type]:
        raise VerificationReviewError("Result code does not match this check type.")

    verification = DriverVerification.objects.select_for_update().get(pk=check.verification_id)
    previous_overall_status = verification.status
    now = timezone.now()
    check.status = status
    check.method = method
    check.result_code = result_code
    check.checked_at = now
    check.reviewed_by = reviewer
    check.save(
        update_fields=[
            "status", "method", "result_code", "checked_at", "reviewed_by",
            "updated_at",
        ]
    )

    check_statuses = list(verification.checks.values_list("status", flat=True))
    required_count = len(DriverVerificationCheck.CheckType.choices)
    if any(value == DriverVerificationCheck.Status.FAILED for value in check_statuses):
        verification.status = DriverVerification.Status.REJECTED
    elif (
        len(check_statuses) == required_count
        and all(value == DriverVerificationCheck.Status.PASSED for value in check_statuses)
    ):
        verification.status = DriverVerification.Status.APPROVED
    else:
        verification.status = DriverVerification.Status.IN_REVIEW
    verification.decided_by = reviewer if verification.status in {
        DriverVerification.Status.APPROVED,
        DriverVerification.Status.REJECTED,
    } else None
    verification.decided_at = now if verification.decided_by else None
    verification.save(
        update_fields=["status", "decided_by", "decided_at", "updated_at"]
    )

    if verification.status != previous_overall_status:
        driver_account = verification.profile.registration.account
        status_titles = {
            DriverVerification.Status.IN_REVIEW: (
                "Verification in review",
                "Your driver verification is being reviewed.",
            ),
            DriverVerification.Status.APPROVED: (
                "Driver verification approved",
                "Your driver verification is approved.",
            ),
            DriverVerification.Status.REJECTED: (
                "Driver verification not approved",
                "Your driver verification was not approved. Please review your verification workspace for the current status.",
            ),
        }
        title, message = status_titles.get(
            verification.status,
            ("Verification status updated", "Your driver verification status has changed."),
        )
        create_notification(
            recipient=driver_account,
            recipient_role=Notification.RecipientRole.DRIVER,
            event_type=f"driver.verification.{verification.status}",
            title=title,
            message=message,
        )

    return check


@transaction.atomic
def record_verified_licence_classes(*, check_id, licence_classes, reviewer):
    """Record only classes confirmed from a presented and validated licence."""
    check = (
        DriverVerificationCheck.objects.select_for_update()
        .filter(pk=check_id)
        .first()
    )
    if check is None:
        raise VerificationReviewError("Verification check not found.")
    if (
        check.check_type != DriverVerificationCheck.CheckType.DRIVING_LICENCE
        or check.status != DriverVerificationCheck.Status.PASSED
        or check.result_code != DriverVerificationCheck.ResultCode.VALID
    ):
        raise VerificationReviewError(
            "Licence classes can only be recorded after the driving licence is validated."
        )
    if not licence_classes:
        raise VerificationReviewError("Provide at least one validated licence class.")

    normalized = []
    for value in licence_classes:
        licence_class = str(value).strip().upper()
        if (
            not licence_class
            or len(licence_class) > 12
            or not licence_class.isalnum()
        ):
            raise VerificationReviewError(
                "Licence classes must contain only letters and numbers, up to 12 characters."
            )
        if licence_class in normalized:
            raise VerificationReviewError("Duplicate licence classes are not allowed.")
        normalized.append(licence_class)

    now = timezone.now()
    VerifiedDriverLicenceClass.objects.filter(
        licence_check=check,
        is_current=True,
    ).update(is_current=False, updated_at=now)

    records = []
    for licence_class in normalized:
        record, _created = VerifiedDriverLicenceClass.objects.update_or_create(
            licence_check=check,
            licence_class=licence_class,
            defaults={
                "is_current": True,
                "verified_at": now,
                "verified_by": reviewer,
            },
        )
        records.append(record)
    return records
