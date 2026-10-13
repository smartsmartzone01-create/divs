from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.operations.models import OperationsMembership
from apps.performance.models import PerformanceEvent, PerformanceEventReview
from apps.performance.services.scoring import apply_approved_event_score


def _require_event_reviewer(actor):
    if not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("An authenticated Operations reviewer is required.")

    allowed_roles = [
        OperationsMembership.Role.ADMIN,
        OperationsMembership.Role.OPERATOR,
    ]
    if not OperationsMembership.objects.filter(
        account=actor,
        role__in=allowed_roles,
    ).exists():
        raise PermissionDenied("Only an approved Operations Admin or Operator may review events.")


@transaction.atomic
def review_performance_event(
    *,
    event_id,
    reviewer,
    decision,
    reason,
    requested_evidence="",
):
    """Record a review decision and score eligible approvals using approved rules."""
    _require_event_reviewer(reviewer)

    allowed_decisions = PerformanceEventReview.Decision.values
    if decision not in allowed_decisions:
        raise ValidationError({"decision": "Choose approve, reject, or request more evidence."})
    if not isinstance(reason, str) or not reason.strip():
        raise ValidationError({"reason": "A reason is required for every review decision."})
    if decision == PerformanceEventReview.Decision.MORE_EVIDENCE:
        if not isinstance(requested_evidence, str) or not requested_evidence.strip():
            raise ValidationError({"requested_evidence": "Describe the additional evidence needed."})

    event = PerformanceEvent.objects.select_for_update().get(pk=event_id)
    if event.status in (
        PerformanceEvent.Status.APPROVED,
        PerformanceEvent.Status.REJECTED,
    ):
        raise ValidationError({"event": "This event already has a final decision."})

    now = timezone.now()
    event.status = decision
    event.reviewed_by = reviewer
    event.reviewed_at = now
    event.decision_reason = reason.strip()
    event.save(
        update_fields=[
            "status",
            "reviewed_by",
            "reviewed_at",
            "decision_reason",
            "updated_at",
        ]
    )

    review = PerformanceEventReview.objects.create(
        event=event,
        decision=decision,
        reason=reason.strip(),
        requested_evidence=requested_evidence.strip() if requested_evidence else "",
        reviewer=reviewer,
    )

    if decision == PerformanceEvent.Status.APPROVED and event.category in (
        PerformanceEvent.Category.POSITIVE,
        PerformanceEvent.Category.NEGATIVE,
    ):
        # If no approved rule or no established calculated score exists, the
        # event remains approved but receives no score effect yet.
        apply_approved_event_score(event_id=event.pk, actor=reviewer)

    return event, review
