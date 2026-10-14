from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.operations.models import OperationsMembership
from apps.operations.permissions import capabilities_for, is_initial_system_superuser
from apps.performance.models import (
    AvailabilityRestriction,
    AvailabilityRestrictionDecision,
    DriverScore,
    PerformanceEvent,
)


LOW_SCORE_RESTRICTION_THRESHOLD = 40


def _membership_role(actor):
    if not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("An authenticated Operations user is required.")
    if is_initial_system_superuser(actor):
        return OperationsMembership.Role.ADMIN
    membership = OperationsMembership.objects.filter(account=actor).first()
    if membership is None or "manage_driver_performance" not in capabilities_for(actor):
        raise PermissionDenied("An active Operations membership is required.")
    return membership.role


@transaction.atomic
def place_critical_incident_restriction(*, event_id, actor, reason):
    """Temporarily restrict availability while a credible critical event is investigated."""
    role = _membership_role(actor)
    if role not in (OperationsMembership.Role.ADMIN, OperationsMembership.Role.OPERATOR):
        raise PermissionDenied("Only Operations Admins or Operators may refer critical incidents.")
    if not isinstance(reason, str) or not reason.strip():
        raise ValidationError({"reason": "Explain why the critical report is credible enough for precautionary review."})

    event = PerformanceEvent.objects.select_for_update().select_related("driver").get(pk=event_id)
    if event.severity != PerformanceEvent.Severity.CRITICAL:
        raise ValidationError({"event": "Only a critical-severity event can trigger this restriction."})
    if event.status == PerformanceEvent.Status.REJECTED:
        raise ValidationError({"event": "A rejected event cannot trigger an availability restriction."})

    existing = AvailabilityRestriction.objects.filter(
        source_event=event,
        kind=AvailabilityRestriction.Kind.CRITICAL_INCIDENT,
        status=AvailabilityRestriction.Status.ACTIVE,
    ).first()
    if existing:
        return existing

    # This is a precautionary review state, not a finding of guilt.
    event.status = PerformanceEvent.Status.UNDER_REVIEW
    event.save(update_fields=["status", "updated_at"])

    restriction = AvailabilityRestriction.objects.create(
        driver=event.driver,
        kind=AvailabilityRestriction.Kind.CRITICAL_INCIDENT,
        reason=reason.strip(),
        source_event=event,
        created_by=actor,
    )
    AvailabilityRestrictionDecision.objects.create(
        restriction=restriction,
        action=AvailabilityRestrictionDecision.Action.PLACED,
        reason=reason.strip(),
        actor=actor,
    )
    return restriction


@transaction.atomic
def apply_low_score_restriction(*, score_id, actor, reason):
    """Restrict hire availability when the effective score is strictly below 40."""
    role = _membership_role(actor)
    if role not in (OperationsMembership.Role.ADMIN, OperationsMembership.Role.OPERATOR):
        raise PermissionDenied("Only Operations Admins or Operators may apply restrictions.")
    if not isinstance(reason, str) or not reason.strip():
        raise ValidationError({"reason": "A reason is required for the restriction."})

    score = DriverScore.objects.select_for_update().select_related("driver").get(pk=score_id)
    effective_score = score.effective_score
    if effective_score is None:
        raise ValidationError({"score": "A restriction cannot be based on an unset score."})
    if effective_score >= LOW_SCORE_RESTRICTION_THRESHOLD:
        return None

    existing = AvailabilityRestriction.objects.filter(
        source_score=score,
        kind=AvailabilityRestriction.Kind.LOW_SCORE,
        status=AvailabilityRestriction.Status.ACTIVE,
    ).first()
    if existing:
        return existing

    restriction = AvailabilityRestriction.objects.create(
        driver=score.driver,
        kind=AvailabilityRestriction.Kind.LOW_SCORE,
        reason=reason.strip(),
        source_score=score,
        created_by=actor,
    )
    AvailabilityRestrictionDecision.objects.create(
        restriction=restriction,
        action=AvailabilityRestrictionDecision.Action.PLACED,
        reason=reason.strip(),
        actor=actor,
    )
    return restriction


@transaction.atomic
def release_availability_restriction(*, restriction_id, actor, reason):
    """Release a restriction with a recorded decision; low-score release is Admin-only."""
    role = _membership_role(actor)
    if role not in (OperationsMembership.Role.ADMIN, OperationsMembership.Role.OPERATOR):
        raise PermissionDenied("Only Operations Admins or Operators may release restrictions.")
    if not isinstance(reason, str) or not reason.strip():
        raise ValidationError({"reason": "A reason is required to release a restriction."})

    restriction = AvailabilityRestriction.objects.select_for_update().get(pk=restriction_id)
    if restriction.status != AvailabilityRestriction.Status.ACTIVE:
        raise ValidationError({"restriction": "This restriction is already released."})
    if (
        restriction.kind == AvailabilityRestriction.Kind.LOW_SCORE
        and role != OperationsMembership.Role.ADMIN
    ):
        raise PermissionDenied("Only an Operations Admin may restore availability after a low-score restriction.")

    restriction.status = AvailabilityRestriction.Status.RELEASED
    restriction.released_by = actor
    restriction.released_at = timezone.now()
    restriction.release_reason = reason.strip()
    restriction.save(
        update_fields=[
            "status",
            "released_by",
            "released_at",
            "release_reason",
        ]
    )
    AvailabilityRestrictionDecision.objects.create(
        restriction=restriction,
        action=AvailabilityRestrictionDecision.Action.RELEASED,
        reason=reason.strip(),
        actor=actor,
    )
    return restriction


def has_active_performance_restriction(*, driver_id):
    """Return whether any performance restriction currently blocks hire availability."""
    return AvailabilityRestriction.objects.filter(
        driver_id=driver_id,
        status=AvailabilityRestriction.Status.ACTIVE,
    ).exists()
