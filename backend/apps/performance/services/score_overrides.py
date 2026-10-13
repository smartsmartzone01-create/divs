from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.operations.models import OperationsMembership
from apps.performance.models import DriverScore, ScoreHistory


def _require_admin(actor):
    if not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("An authenticated Admin account is required.")

    is_admin = OperationsMembership.objects.filter(
        account=actor,
        role=OperationsMembership.Role.ADMIN,
    ).exists()
    if not is_admin:
        raise PermissionDenied("Only an approved Operations Admin may override a score.")


@transaction.atomic
def override_driver_score(*, score_id, actor, new_score, reason):
    """Set an Admin override without replacing the automatic calculated score.

    Creates a score-history entry in the same transaction as the current override
    state update. Availability restrictions are intentionally not changed here.
    """
    _require_admin(actor)

    if isinstance(new_score, bool) or not isinstance(new_score, int):
        raise ValidationError({"new_score": "Enter a whole-number score from 0 to 100."})
    if not 0 <= new_score <= 100:
        raise ValidationError({"new_score": "Score must be between 0 and 100."})
    if not isinstance(reason, str) or not reason.strip():
        raise ValidationError({"reason": "A reason is required for every manual override."})

    score = DriverScore.objects.select_for_update().get(pk=score_id)
    previous_score = score.effective_score
    now = timezone.now()

    score.manual_override_score = new_score
    score.manual_override_reason = reason.strip()
    score.manual_override_by = actor
    score.manual_override_at = now
    score.save(
        update_fields=[
            "manual_override_score",
            "manual_override_reason",
            "manual_override_by",
            "manual_override_at",
            "updated_at",
        ]
    )

    history = ScoreHistory.objects.create(
        score=score,
        change_type=ScoreHistory.ChangeType.MANUAL_OVERRIDE,
        previous_score=previous_score,
        new_score=new_score,
        reason=reason.strip(),
        actor=actor,
    )
    return score, history
