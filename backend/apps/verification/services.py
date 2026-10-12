from django.db import transaction
from django.utils import timezone

from apps.verification.models import DriverVerification, DriverVerificationCheck


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
    review_note="",
):
    """Record a minimal outcome only; never pass through or persist source payloads."""
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
        .select_related("verification")
        .filter(pk=check_id)
        .first()
    )
    if check is None:
        raise VerificationReviewError("Verification check not found.")
    if result_code and result_code not in compatible_results[check.check_type]:
        raise VerificationReviewError("Result code does not match this check type.")

    now = timezone.now()
    check.status = status
    check.method = method
    check.result_code = result_code
    check.checked_at = now
    check.reviewed_by = reviewer
    check.review_note = review_note.strip()[:500]
    check.save(
        update_fields=[
            "status", "method", "result_code", "checked_at", "reviewed_by",
            "review_note", "updated_at",
        ]
    )

    verification = DriverVerification.objects.select_for_update().get(pk=check.verification_id)
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
    return check
