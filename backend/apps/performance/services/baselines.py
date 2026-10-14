from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.operations.models import OperationsMembership
from apps.operations.permissions import capabilities_for, is_initial_system_superuser
from apps.performance.models import DriverScore, ScoreHistory


BASELINE_SCORE = 80


def _require_admin(actor):
    if not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("An authenticated Operations Admin is required.")
    if is_initial_system_superuser(actor):
        return
    if (
        not OperationsMembership.objects.filter(account=actor, role=OperationsMembership.Role.ADMIN).exists()
        or "manage_driver_performance" not in capabilities_for(actor)
    ):
        raise PermissionDenied("Only an active Operations Admin may establish a performance baseline.")


@transaction.atomic
def establish_driver_baseline(
    *,
    score_id,
    actor,
    verification_confirmed,
    history_reviewed,
    applicable_history_found,
    reason,
):
    """Establish the agreed 80-point baseline after explicit Admin eligibility checks.

    Until the no-history policy is finalized, a driver with no applicable history
    remains unscored. This service deliberately does not infer eligibility from
    missing records.
    """
    _require_admin(actor)
    if verification_confirmed is not True:
        raise ValidationError({"verification_confirmed": "Driver verification must be confirmed first."})
    if history_reviewed is not True:
        raise ValidationError({"history_reviewed": "Applicable performance history must be reviewed."})
    if applicable_history_found is not True:
        raise ValidationError({
            "applicable_history_found": (
                "No applicable history was found. The baseline policy for drivers without history "
                "has not been finalized, so the score must remain unset."
            )
        })
    if not isinstance(reason, str) or not reason.strip():
        raise ValidationError({"reason": "Record why this driver qualifies for the baseline."})

    score = DriverScore.objects.select_for_update().get(pk=score_id)
    if score.calculated_score is not None:
        raise ValidationError({"score": "A calculated score is already established."})
    if ScoreHistory.objects.filter(score=score).exists():
        raise ValidationError({
            "score": "Score history already exists. Use a reviewed recalculation workflow instead."
        })

    score.calculated_score = BASELINE_SCORE
    score.calculation_updated_at = timezone.now()
    score.save(update_fields=["calculated_score", "calculation_updated_at", "updated_at"])
    history = ScoreHistory.objects.create(
        score=score,
        change_type=ScoreHistory.ChangeType.BASELINE,
        previous_score=None,
        new_score=BASELINE_SCORE,
        reason=reason.strip(),
        actor=actor,
    )
    return score, history
