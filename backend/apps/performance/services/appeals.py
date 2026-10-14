from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.operations.models import OperationsMembership
from apps.operations.permissions import is_initial_system_superuser
from apps.performance.models import (
    PerformanceAppeal,
    PerformanceAppealDecision,
    PerformanceEvent,
)


def _require_appeal_reviewer(actor):
    if not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("An authenticated Operations reviewer is required.")
    if is_initial_system_superuser(actor):
        return
    if not OperationsMembership.objects.filter(
        account=actor,
        role__in=[OperationsMembership.Role.ADMIN, OperationsMembership.Role.OPERATOR],
    ).exists():
        raise PermissionDenied("Only an approved Operations Admin or Operator may decide appeals.")


@transaction.atomic
def submit_performance_appeal(*, event_id, appellant, reason, evidence_references=None):
    """Create a pending appeal without changing score or availability restrictions."""
    if not getattr(appellant, "is_authenticated", False):
        raise PermissionDenied("Sign in to submit an appeal.")
    if not isinstance(reason, str) or not reason.strip():
        raise ValidationError({"reason": "Explain why the event decision is being challenged."})
    if evidence_references is None:
        evidence_references = []
    if not isinstance(evidence_references, list):
        raise ValidationError({"evidence_references": "Provide a list of evidence references."})

    event = PerformanceEvent.objects.select_for_update().select_related(
        "driver__registration"
    ).get(pk=event_id)
    if event.driver.registration.account_id != appellant.pk:
        raise PermissionDenied("Only the driver associated with this event may appeal it.")
    if event.status not in (
        PerformanceEvent.Status.APPROVED,
        PerformanceEvent.Status.REJECTED,
    ):
        raise ValidationError({"event": "Only an event with a final decision can be appealed."})

    if PerformanceAppeal.objects.filter(
        event=event,
        status=PerformanceAppeal.Status.PENDING,
    ).exists():
        raise ValidationError({"event": "This event already has a pending appeal."})

    appeal = PerformanceAppeal.objects.create(
        event=event,
        appellant=appellant,
        reason=reason.strip(),
        evidence_references=evidence_references,
    )
    # Deliberately do not modify DriverScore or AvailabilityRestriction here.
    return appeal


@transaction.atomic
def decide_performance_appeal(*, appeal_id, reviewer, decision, reason):
    """Record an appeal decision; a successful appeal flags correction for follow-up."""
    _require_appeal_reviewer(reviewer)
    if decision not in (
        PerformanceAppeal.Status.UPHELD,
        PerformanceAppeal.Status.DENIED,
    ):
        raise ValidationError({"decision": "Choose upheld or denied."})
    if not isinstance(reason, str) or not reason.strip():
        raise ValidationError({"reason": "A reason is required for the appeal decision."})

    appeal = PerformanceAppeal.objects.select_for_update().get(pk=appeal_id)
    if appeal.status != PerformanceAppeal.Status.PENDING:
        raise ValidationError({"appeal": "Only a pending appeal can be decided."})

    appeal.status = decision
    appeal.decided_by = reviewer
    appeal.decided_at = timezone.now()
    appeal.decision_reason = reason.strip()
    if decision == PerformanceAppeal.Status.UPHELD:
        appeal.correction_required = True
    appeal.save(
        update_fields=[
            "status",
            "decided_by",
            "decided_at",
            "decision_reason",
            "correction_required",
            "updated_at",
        ]
    )
    history = PerformanceAppealDecision.objects.create(
        appeal=appeal,
        status=decision,
        reason=reason.strip(),
        reviewer=reviewer,
    )
    # Current score and restrictions intentionally remain unchanged until a
    # traceable correction workflow recalculates score effects.
    return appeal, history
