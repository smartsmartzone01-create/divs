from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.operations.models import OperationsMembership
from apps.performance.models import (
    DriverScore,
    PerformanceAppeal,
    PerformanceEventScoreApplication,
    PerformanceScoreCorrection,
    ScoreHistory,
)


def _require_admin(actor):
    if not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("An authenticated Operations Admin is required.")
    if not OperationsMembership.objects.filter(
        account=actor,
        role=OperationsMembership.Role.ADMIN,
    ).exists():
        raise PermissionDenied("Only an Operations Admin may apply appeal corrections.")


def _recalculate_without_corrected_events(score):
    """Replay immutable event applications from their earliest recorded starting score."""
    applications = list(
        PerformanceEventScoreApplication.objects.filter(score=score).order_by("applied_at", "pk")
    )
    if not applications:
        return score.calculated_score

    corrected_event_ids = PerformanceScoreCorrection.objects.filter(
        score=score
    ).values_list("event_id", flat=True)
    corrected_event_ids = set(corrected_event_ids)

    # The earliest application preserves the calculated score immediately before
    # any scored event. Replay the immutable point deltas, excluding appealed events
    # already corrected and the event being corrected by the caller.
    recalculated = applications[0].previous_score
    for application in applications:
        if application.event_id in corrected_event_ids:
            continue
        recalculated = max(0, min(100, recalculated + application.points_delta))
    return recalculated


@transaction.atomic
def correct_score_after_upheld_appeal(*, appeal_id, actor, reason):
    """Admin-only, auditable correction for an upheld appeal.

    The original event and score-application ledger remain untouched. The current
    calculated score is replayed without the overturned event. Manual override and
    availability restrictions are not changed by this service.
    """
    _require_admin(actor)
    if not isinstance(reason, str) or not reason.strip():
        raise ValidationError({"reason": "Explain the score correction."})

    appeal = PerformanceAppeal.objects.select_for_update().select_related(
        "event__driver"
    ).get(pk=appeal_id)
    if appeal.status != PerformanceAppeal.Status.UPHELD:
        raise ValidationError({"appeal": "Only an upheld appeal can be corrected."})
    if not appeal.correction_required:
        raise ValidationError({"appeal": "This appeal does not have an outstanding correction."})
    if PerformanceScoreCorrection.objects.filter(appeal=appeal).exists():
        raise ValidationError({"appeal": "A correction audit record already exists for this appeal."})

    score = DriverScore.objects.select_for_update().filter(
        driver=appeal.event.driver
    ).first()
    application = PerformanceEventScoreApplication.objects.filter(event=appeal.event).first()

    if score is None or score.calculated_score is None:
        if application is not None:
            raise ValidationError({
                "score": "The event has a score application but the current calculated score is unset. Admin review is required."
            })
        previous = None if score is None else score.calculated_score
        correction = PerformanceScoreCorrection.objects.create(
            appeal=appeal,
            event=appeal.event,
            score=score,
            previous_calculated_score=previous,
            new_calculated_score=previous,
            removed_points_delta=None,
            reason=reason.strip(),
            actor=actor,
        )
    else:
        previous = score.calculated_score
        if application is None:
            # The appealed event never changed the score, so record the outcome
            # without manufacturing a score change.
            recalculated = previous
        else:
            recalculated = _recalculate_without_corrected_events(score)

        correction = PerformanceScoreCorrection.objects.create(
            appeal=appeal,
            event=appeal.event,
            score=score,
            previous_calculated_score=previous,
            new_calculated_score=recalculated,
            removed_points_delta=None if application is None else application.points_delta,
            reason=reason.strip(),
            actor=actor,
        )

        if recalculated != previous:
            score.calculated_score = recalculated
            score.calculation_updated_at = timezone.now()
            score.save(update_fields=["calculated_score", "calculation_updated_at", "updated_at"])
            ScoreHistory.objects.create(
                score=score,
                event=appeal.event,
                change_type=ScoreHistory.ChangeType.CORRECTION,
                previous_score=previous,
                new_score=recalculated,
                reason=reason.strip(),
                rule_reference=f"appeal:{appeal.pk}",
                actor=actor,
            )

    appeal.correction_required = False
    appeal.save(update_fields=["correction_required", "updated_at"])
    # Intentionally do not release active restrictions or clear manual overrides.
    return correction
