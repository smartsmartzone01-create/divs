from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.performance.models import (
    DriverScore,
    PerformanceEvent,
    PerformanceEventScoreApplication,
    PerformanceScoringRule,
    ScoreHistory,
)
from apps.performance.services.availability import apply_low_score_restriction


@transaction.atomic
def apply_approved_event_score(*, event_id, actor=None):
    """Apply one approved positive/negative event using its currently approved rule.

    Returns None when no approved matching rule or established calculated score exists.
    An event can be applied only once; rule applications and score history are preserved.
    """
    event = PerformanceEvent.objects.select_for_update().select_related("driver").get(pk=event_id)
    if event.status != PerformanceEvent.Status.APPROVED:
        raise ValidationError({"event": "Only an approved event can affect the score."})
    if event.category not in (
        PerformanceEvent.Category.POSITIVE,
        PerformanceEvent.Category.NEGATIVE,
    ):
        raise ValidationError({"event": "Correction events require the separate correction workflow."})

    existing = PerformanceEventScoreApplication.objects.filter(event=event).first()
    if existing:
        return existing

    rule = PerformanceScoringRule.objects.filter(
        category=event.category,
        event_code=event.event_code,
        severity=event.severity,
        status=PerformanceScoringRule.Status.APPROVED,
    ).first()
    if rule is None:
        return None

    score = DriverScore.objects.select_for_update().filter(driver=event.driver).first()
    if score is None or score.calculated_score is None:
        # No automatic baseline is inferred from missing history.
        return None

    previous_score = score.calculated_score
    new_score = max(0, min(100, previous_score + rule.points_delta))
    reason = f"Applied approved scoring rule '{rule.name}' to event {event.pk}."

    score.calculated_score = new_score
    score.calculation_updated_at = timezone.now()
    score.save(update_fields=["calculated_score", "calculation_updated_at", "updated_at"])

    application = PerformanceEventScoreApplication.objects.create(
        event=event,
        score=score,
        rule=rule,
        rule_name_snapshot=rule.name,
        points_delta=rule.points_delta,
        previous_score=previous_score,
        new_score=new_score,
        reason=reason,
    )
    ScoreHistory.objects.create(
        score=score,
        event=event,
        change_type=ScoreHistory.ChangeType.EVENT,
        previous_score=previous_score,
        new_score=new_score,
        reason=reason,
        rule_reference=str(rule.pk),
        actor=actor,
    )

    # Apply a restriction if the effective score is below 40. Never release an
    # existing restriction automatically when a score rises or is overridden.
    if score.effective_score is not None and score.effective_score < 40 and actor is not None:
        apply_low_score_restriction(
            score_id=score.pk,
            actor=actor,
            reason=f"Effective performance score is {score.effective_score}, below 40.",
        )

    return application
