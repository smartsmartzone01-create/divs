from django.db import transaction
from django.utils import timezone

from apps.notifications.models import Notification
from apps.notifications.services import create_notification
from apps.profiles.models import DriverProfile
from apps.verification.models import (
    DriverVerification,
    DriverVerificationCheck,
    DriverVerificationEvent,
    VerifiedDriverLicenceClass,
)


class VerificationReviewError(Exception):
    """Raised when a verification workflow action is invalid."""


SUCCESSFUL_RESULTS = {
    DriverVerificationCheck.CheckType.NATIONAL_IDENTITY: DriverVerificationCheck.ResultCode.MATCH,
    DriverVerificationCheck.CheckType.DRIVING_LICENCE: DriverVerificationCheck.ResultCode.VALID,
    DriverVerificationCheck.CheckType.TRAFFIC_RECORDS: DriverVerificationCheck.ResultCode.CLEAR,
    DriverVerificationCheck.CheckType.ACCIDENT_RECORDS: DriverVerificationCheck.ResultCode.CLEAR,
}


def _notify_driver(verification, event, title, message):
    account = verification.profile.registration.account
    create_notification(
        recipient=account,
        recipient_role=Notification.RecipientRole.DRIVER,
        event_type=event,
        title=title,
        message=message,
    )


@transaction.atomic
def review_driver_check(*, check_id, reviewer, status, method=DriverVerificationCheck.Method.MANUAL, result_code="", review_notes=""):
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
            DriverVerificationCheck.ResultCode.MATCH, DriverVerificationCheck.ResultCode.MISMATCH,
            DriverVerificationCheck.ResultCode.INCONCLUSIVE,
        },
        DriverVerificationCheck.CheckType.DRIVING_LICENCE: {
            DriverVerificationCheck.ResultCode.VALID, DriverVerificationCheck.ResultCode.INVALID,
            DriverVerificationCheck.ResultCode.INCONCLUSIVE,
        },
        DriverVerificationCheck.CheckType.TRAFFIC_RECORDS: {
            DriverVerificationCheck.ResultCode.CLEAR, DriverVerificationCheck.ResultCode.RECORD_FOUND,
            DriverVerificationCheck.ResultCode.INCONCLUSIVE,
        },
        DriverVerificationCheck.CheckType.ACCIDENT_RECORDS: {
            DriverVerificationCheck.ResultCode.CLEAR, DriverVerificationCheck.ResultCode.RECORD_FOUND,
            DriverVerificationCheck.ResultCode.INCONCLUSIVE,
        },
    }

    check = (
        DriverVerificationCheck.objects.select_for_update()
        .select_related("verification", "verification__profile", "verification__profile__registration")
        .filter(pk=check_id).first()
    )
    if check is None:
        raise VerificationReviewError("Verification check not found.")
    if result_code and result_code not in compatible_results[check.check_type]:
        raise VerificationReviewError("Result code does not match this check type.")
    if status in {DriverVerificationCheck.Status.PASSED, DriverVerificationCheck.Status.FAILED} and not result_code:
        raise VerificationReviewError("A result code is required when a check passes or fails.")
    if status == DriverVerificationCheck.Status.PASSED and result_code != SUCCESSFUL_RESULTS[check.check_type]:
        raise VerificationReviewError("A check can only pass when its result confirms successful verification.")
    if status == DriverVerificationCheck.Status.FAILED and result_code == SUCCESSFUL_RESULTS[check.check_type]:
        raise VerificationReviewError("A successful result cannot be recorded as failed.")
    if result_code == DriverVerificationCheck.ResultCode.INCONCLUSIVE and status in {
        DriverVerificationCheck.Status.PASSED, DriverVerificationCheck.Status.FAILED,
    }:
        raise VerificationReviewError("An inconclusive result requires further review.")

    verification = DriverVerification.objects.select_for_update().get(pk=check.verification_id)
    if verification.status == DriverVerification.Status.REJECTED:
        raise VerificationReviewError("A rejected verification cannot be changed.")
    now = timezone.now()
    previous_check_status = check.status
    check.status = status
    check.method = method
    check.result_code = result_code
    check.review_notes = review_notes.strip()
    check.checked_at = now
    check.reviewed_by = reviewer
    check.save(update_fields=[
        "status", "method", "result_code", "review_notes", "checked_at",
        "reviewed_by", "updated_at",
    ])
    DriverVerificationEvent.objects.create(
        verification=verification, check=check, actor=reviewer,
        event_type=DriverVerificationEvent.EventType.CHECK_REVIEWED,
        previous_status=previous_check_status, new_status=status,
        notes=check.review_notes,
    )

    # Findings never approve or reject the overall application.
    if verification.status == DriverVerification.Status.PENDING:
        verification.status = DriverVerification.Status.IN_REVIEW
        verification.save(update_fields=["status", "updated_at"])
        _notify_driver(
            verification, "driver.verification.in_review",
            "Verification in review", "Your driver verification is being reviewed.",
        )
    return check


@transaction.atomic
def decide_driver_verification(*, verification_id, actor, decision, reason=""):
    verification = (
        DriverVerification.objects.select_for_update()
        .select_related("profile", "profile__registration", "profile__registration__account")
        .prefetch_related("checks__verified_licence_classes")
        .filter(pk=verification_id).first()
    )
    if verification is None:
        raise VerificationReviewError("Driver verification not found.")
    if verification.status in {DriverVerification.Status.APPROVED, DriverVerification.Status.REJECTED}:
        raise VerificationReviewError("A final verification decision has already been recorded.")

    if decision == DriverVerification.Status.APPROVED:
        if not verification.checks_are_complete:
            raise VerificationReviewError("All four verification checks must pass before approval.")
        licence_check = verification.checks.filter(
            check_type=DriverVerificationCheck.CheckType.DRIVING_LICENCE,
            status=DriverVerificationCheck.Status.PASSED,
            result_code=DriverVerificationCheck.ResultCode.VALID,
        ).first()
        if licence_check is None or not licence_check.verified_licence_classes.filter(is_current=True).exists():
            raise VerificationReviewError("At least one current verified licence class is required.")
        title = "Driver verification approved"
        message = "Your driver verification is approved. Your profile will appear publicly only after availability is activated."
        event = "driver.verification.approved"
    elif decision == DriverVerification.Status.REJECTED:
        if not reason.strip():
            raise VerificationReviewError("A reason is required when rejecting a verification.")
        title = "Driver verification not approved"
        message = "Your driver verification was not approved. Please review your verification workspace for the current status."
        event = "driver.verification.rejected"
    else:
        raise VerificationReviewError("Unsupported final decision.")

    previous_status = verification.status
    verification.status = decision
    verification.decided_by = actor
    verification.decided_at = timezone.now()
    verification.decision_reason = reason.strip()
    verification.save(update_fields=["status", "decided_by", "decided_at", "decision_reason", "updated_at"])
    DriverVerificationEvent.objects.create(
        verification=verification, actor=actor,
        event_type=(DriverVerificationEvent.EventType.APPROVED if decision == DriverVerification.Status.APPROVED else DriverVerificationEvent.EventType.REJECTED),
        previous_status=previous_status, new_status=decision, notes=reason.strip(),
    )
    _notify_driver(verification, event, title, message)
    return verification


@transaction.atomic
def activate_driver_availability(*, verification_id, actor):
    verification = (
        DriverVerification.objects.select_for_update()
        .select_related("profile", "profile__registration", "profile__registration__account")
        .prefetch_related("checks__verified_licence_classes")
        .filter(pk=verification_id).first()
    )
    if verification is None:
        raise VerificationReviewError("Driver verification not found.")
    if verification.status != DriverVerification.Status.APPROVED:
        raise VerificationReviewError("Only an approved driver can be activated.")
    if not verification.checks_are_complete:
        raise VerificationReviewError("All required verification checks must still be passed.")
    licence_check = verification.checks.filter(
        check_type=DriverVerificationCheck.CheckType.DRIVING_LICENCE,
        status=DriverVerificationCheck.Status.PASSED,
        result_code=DriverVerificationCheck.ResultCode.VALID,
    ).first()
    if licence_check is None or not licence_check.verified_licence_classes.filter(is_current=True).exists():
        raise VerificationReviewError("A current verified licence class is required before activation.")
    if verification.profile.status == DriverProfile.Status.CLOSED:
        raise VerificationReviewError("A closed driver profile cannot be activated.")
    if verification.profile.status == DriverProfile.Status.SUSPENDED:
        raise VerificationReviewError("A suspended driver profile cannot be activated.")
    if verification.profile.status == DriverProfile.Status.ACTIVE:
        raise VerificationReviewError("Driver availability is already active.")
    previous_profile_status = verification.profile.status
    verification.profile.status = DriverProfile.Status.ACTIVE
    verification.profile.availability_activated_at = timezone.now()
    verification.profile.availability_activated_by = actor
    verification.profile.save(update_fields=["status", "availability_activated_at", "availability_activated_by", "updated_at"])
    DriverVerificationEvent.objects.create(
        verification=verification, actor=actor,
        event_type=DriverVerificationEvent.EventType.AVAILABILITY_ACTIVATED,
        previous_status=previous_profile_status,
        new_status=DriverProfile.Status.ACTIVE,
    )
    _notify_driver(
        verification, "driver.availability.activated",
        "Driver profile activated", "Your verified driver profile is now available in the public directory.",
    )
    return verification.profile


@transaction.atomic
def record_verified_licence_classes(*, check_id, licence_classes, reviewer):
    check = DriverVerificationCheck.objects.select_for_update().filter(pk=check_id).first()
    if check is None:
        raise VerificationReviewError("Verification check not found.")
    if (
        check.check_type != DriverVerificationCheck.CheckType.DRIVING_LICENCE
        or check.status != DriverVerificationCheck.Status.PASSED
        or check.result_code != DriverVerificationCheck.ResultCode.VALID
    ):
        raise VerificationReviewError("Licence classes can only be recorded after the driving licence is validated.")
    if not licence_classes:
        raise VerificationReviewError("Provide at least one validated licence class.")

    normalized = []
    for value in licence_classes:
        item = str(value).strip().upper()
        if not item or len(item) > 12 or not item.isalnum():
            raise VerificationReviewError("Licence classes must contain only letters and numbers, up to 12 characters.")
        if item in normalized:
            raise VerificationReviewError("Duplicate licence classes are not allowed.")
        normalized.append(item)

    now = timezone.now()
    VerifiedDriverLicenceClass.objects.filter(licence_check=check, is_current=True).update(is_current=False, updated_at=now)
    records = []
    for item in normalized:
        record, _created = VerifiedDriverLicenceClass.objects.update_or_create(
            licence_check=check, licence_class=item,
            defaults={"is_current": True, "verified_at": now, "verified_by": reviewer},
        )
        records.append(record)
    return records
