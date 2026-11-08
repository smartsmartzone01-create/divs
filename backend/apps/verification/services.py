from django.conf import settings
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
    DriverVerificationEvidence,
    DriverVerificationEvidenceEvent,
    GovernmentVerificationAttempt,
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
    # Government API outcomes must use a dedicated trusted integration path;
    # this human review service must never accept a caller-selected API method.
    if method != DriverVerificationCheck.Method.MANUAL:
        raise VerificationReviewError("Government API results cannot be recorded through manual review.")
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

    if status == DriverVerificationCheck.Status.PASSED and not check.has_trusted_supporting_record(
        method=DriverVerificationCheck.Method.MANUAL
    ):
        raise VerificationReviewError(
            "A manual check can pass only while matching accepted evidence is valid and available."
        )

    verification = DriverVerification.objects.select_for_update().get(pk=check.verification_id)
    if verification.status in {DriverVerification.Status.APPROVED, DriverVerification.Status.REJECTED}:
        raise VerificationReviewError("A final verification decision has been recorded; check findings are locked.")
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
        verification=verification, verification_check=check, actor=reviewer,
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
def record_government_api_result(
    *,
    check_id,
    provider,
    provider_reference,
    outcome,
    result_code="",
):
    """Record a normalized result delivered by a trusted server-side API adapter.

    This function is deliberately not exposed through a public DRF endpoint.
    Adapters must authenticate the provider and normalize its response before
    calling it. Only provider references and normalized outcomes are retained.
    """
    provider = str(provider or "").strip()
    provider_reference = str(provider_reference or "").strip()
    if not provider or len(provider) > 80:
        raise VerificationReviewError("A valid government API provider is required.")
    if not provider_reference or len(provider_reference) > 255:
        raise VerificationReviewError("A provider request reference is required.")
    if outcome not in GovernmentVerificationAttempt.Outcome.values:
        raise VerificationReviewError("Unsupported government API outcome.")
    check = (
        DriverVerificationCheck.objects.select_for_update()
        .select_related("verification")
        .filter(pk=check_id)
        .first()
    )
    if check is None:
        raise VerificationReviewError("Verification check not found.")
    verification = DriverVerification.objects.select_for_update().get(pk=check.verification_id)
    if verification.status in {
        DriverVerification.Status.APPROVED,
        DriverVerification.Status.REJECTED,
    }:
        raise VerificationReviewError("A final verification decision has been recorded; check findings are locked.")

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
    if result_code and result_code not in compatible_results[check.check_type]:
        raise VerificationReviewError("Government result code does not match this check type.")

    success_code = SUCCESSFUL_RESULTS[check.check_type]
    if outcome == GovernmentVerificationAttempt.Outcome.MATCHED:
        if result_code != success_code:
            raise VerificationReviewError("A matched API outcome requires the successful result code.")
        check_status = DriverVerificationCheck.Status.PASSED
    elif outcome == GovernmentVerificationAttempt.Outcome.NOT_MATCHED:
        if not result_code or result_code in {success_code, DriverVerificationCheck.ResultCode.INCONCLUSIVE}:
            raise VerificationReviewError("A negative API outcome requires a compatible negative result code.")
        check_status = DriverVerificationCheck.Status.FAILED
    elif outcome == GovernmentVerificationAttempt.Outcome.INCONCLUSIVE:
        if result_code != DriverVerificationCheck.ResultCode.INCONCLUSIVE:
            raise VerificationReviewError("An inconclusive API outcome requires the inconclusive result code.")
        check_status = DriverVerificationCheck.Status.NEEDS_REVIEW
    else:
        result_code = ""
        check_status = DriverVerificationCheck.Status.UNAVAILABLE

    existing_attempt = GovernmentVerificationAttempt.objects.filter(
        provider=provider,
        provider_reference=provider_reference,
    ).first()
    if existing_attempt is not None:
        if (
            existing_attempt.verification_check_id == check.id
            and existing_attempt.outcome == outcome
            and existing_attempt.result_code == result_code
            and check.method == DriverVerificationCheck.Method.GOVERNMENT_API
            and check.result_code == result_code
        ):
            return check
        raise VerificationReviewError("This government provider reference has already been used.")

    now = timezone.now()
    GovernmentVerificationAttempt.objects.create(
        verification_check=check,
        provider=provider,
        provider_reference=provider_reference,
        outcome=outcome,
        result_code=result_code,
        completed_at=now,
    )
    previous_status = check.status
    check.status = check_status
    check.method = DriverVerificationCheck.Method.GOVERNMENT_API
    check.result_code = result_code
    check.review_notes = f"Government provider: {provider}; reference: {provider_reference}; outcome: {outcome}."
    check.checked_at = now
    check.reviewed_by = None
    check.save(update_fields=[
        "status", "method", "result_code", "review_notes", "checked_at",
        "reviewed_by", "updated_at",
    ])
    DriverVerificationEvent.objects.create(
        verification=verification,
        verification_check=check,
        actor=None,
        event_type=DriverVerificationEvent.EventType.GOVERNMENT_API_RESULT,
        previous_status=previous_status,
        new_status=check_status,
        notes=f"Provider: {provider}; reference: {provider_reference}; outcome: {outcome}.",
    )
    if verification.status == DriverVerification.Status.PENDING:
        verification.status = DriverVerification.Status.IN_REVIEW
        verification.save(update_fields=["status", "updated_at"])
        _notify_driver(
            verification, "driver.verification.in_review",
            "Verification in review", "Your driver verification is being reviewed.",
        )
    return check


@transaction.atomic
def review_verification_evidence(*, evidence_id, reviewer, decision, review_notes=""):
    """Accept or reject submitted evidence without changing its security scan state."""
    allowed_decisions = {
        DriverVerificationEvidence.Status.ACCEPTED,
        DriverVerificationEvidence.Status.REJECTED,
    }
    if decision not in allowed_decisions:
        raise VerificationReviewError("Unsupported evidence review decision.")
    if decision == DriverVerificationEvidence.Status.REJECTED and not review_notes.strip():
        raise VerificationReviewError("A reason is required when rejecting evidence.")

    evidence = (
        DriverVerificationEvidence.objects.select_for_update()
        .select_related("verification_check__verification")
        .filter(pk=evidence_id)
        .first()
    )
    if evidence is None:
        raise VerificationReviewError("Verification evidence not found.")
    verification = DriverVerification.objects.select_for_update().get(
        pk=evidence.verification_check.verification_id
    )
    if verification.status in {
        DriverVerification.Status.APPROVED,
        DriverVerification.Status.REJECTED,
    }:
        raise VerificationReviewError("Evidence is locked after a final verification decision.")
    if evidence.status not in {
        DriverVerificationEvidence.Status.SUBMITTED,
        DriverVerificationEvidence.Status.UNDER_REVIEW,
    }:
        raise VerificationReviewError("Only newly submitted evidence can be reviewed.")
    if evidence.storage_deleted_at is not None:
        raise VerificationReviewError("Deleted evidence cannot be reviewed.")
    if evidence.expires_at is not None and evidence.expires_at <= timezone.now():
        raise VerificationReviewError("Expired evidence cannot be accepted or rejected.")
    if evidence.evidence_type != evidence.verification_check.check_type:
        raise VerificationReviewError("Evidence type does not match its verification check.")
    if not evidence.events.filter(actor=reviewer, event_type="file_accessed").exists():
        raise VerificationReviewError("Open the evidence file before recording a review decision.")
    if evidence.scan_status in {
        DriverVerificationEvidence.ScanStatus.INFECTED,
        DriverVerificationEvidence.ScanStatus.ERROR,
    }:
        raise VerificationReviewError("Evidence blocked by security scanning cannot be accepted.")
    development_scan_bypass = (
        settings.DEBUG
        and settings.DIVS_ALLOW_UNSCANNED_EVIDENCE_ACCESS
        and evidence.scan_status == DriverVerificationEvidence.ScanStatus.PENDING
    )
    if (
        evidence.scan_status != DriverVerificationEvidence.ScanStatus.CLEAN
        and not development_scan_bypass
    ):
        raise VerificationReviewError("Evidence must pass the security scan before it can be accepted.")
    if not evidence.storage_key:
        raise VerificationReviewError("Evidence has no stored private file and cannot be accepted.")

    previous_status = evidence.status
    evidence.status = decision
    evidence.reviewed_by = reviewer
    evidence.reviewed_at = timezone.now()
    evidence.review_notes = review_notes.strip()
    evidence.save(update_fields=[
        "status", "reviewed_by", "reviewed_at", "review_notes", "updated_at",
    ])
    DriverVerificationEvidenceEvent.objects.create(
        evidence=evidence,
        actor=reviewer,
        event_type="reviewed",
        previous_status=previous_status,
        new_status=decision,
        notes=evidence.review_notes,
    )
    return evidence


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
        check.verification.status in {DriverVerification.Status.APPROVED, DriverVerification.Status.REJECTED}
    ):
        raise VerificationReviewError("Licence classes cannot be changed after a final verification decision.")
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

    DriverVerificationEvent.objects.create(
        verification=check.verification,
        verification_check=check,
        actor=reviewer,
        event_type=DriverVerificationEvent.EventType.LICENCE_CLASSES_RECORDED,
        new_status=check.status,
        notes="Verified licence classes recorded: " + ", ".join(normalized),
    )
    return records
