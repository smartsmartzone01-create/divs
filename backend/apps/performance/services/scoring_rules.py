from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.operations.models import OperationsMembership
from apps.operations.permissions import capabilities_for, is_initial_system_superuser
from apps.performance.models import PerformanceScoringRule


def _require_admin(actor):
    if not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("An authenticated Operations Admin is required.")
    if is_initial_system_superuser(actor):
        return
    membership = OperationsMembership.objects.filter(
        account=actor, role=OperationsMembership.Role.ADMIN
    ).first()
    if membership is None or "manage_driver_performance" not in capabilities_for(actor):
        raise PermissionDenied("Only an active Operations Admin may manage scoring rules.")


def _validate_rule_values(*, category, event_code, points_delta, name, reason):
    if category not in PerformanceScoringRule.Category.values:
        raise ValidationError({"category": "Choose a positive or negative event category."})
    if not isinstance(event_code, str) or not event_code.strip():
        raise ValidationError({"event_code": "A stable event code is required."})
    if len(event_code.strip()) > 64 or any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-_." for char in event_code.strip().lower()):
        raise ValidationError({"event_code": "Use up to 64 lowercase letters, numbers, hyphens, underscores, or dots."})
    if isinstance(points_delta, bool) or not isinstance(points_delta, int):
        raise ValidationError({"points_delta": "Enter a whole-number point change."})
    if not -100 <= points_delta <= 100:
        raise ValidationError({"points_delta": "Point change must be between -100 and 100."})
    if category == PerformanceScoringRule.Category.POSITIVE and points_delta <= 0:
        raise ValidationError({"points_delta": "Positive rules must add points."})
    if category == PerformanceScoringRule.Category.NEGATIVE and points_delta >= 0:
        raise ValidationError({"points_delta": "Negative rules must subtract points."})
    if not isinstance(name, str) or not name.strip():
        raise ValidationError({"name": "A rule name is required."})
    if not isinstance(reason, str) or not reason.strip():
        raise ValidationError({"reason": "Explain why this scoring rule is proposed."})


@transaction.atomic
def propose_scoring_rule(
    *,
    actor,
    name,
    category,
    event_code,
    severity="",
    points_delta,
    reason,
):
    """Create an inactive proposal. Proposals never affect score calculations."""
    _require_admin(actor)
    _validate_rule_values(
        category=category,
        event_code=event_code,
        points_delta=points_delta,
        name=name,
        reason=reason,
    )
    allowed_severities = {"", "minor", "serious", "critical"}
    if severity not in allowed_severities:
        raise ValidationError({"severity": "Choose a supported severity."})

    return PerformanceScoringRule.objects.create(
        name=name.strip(),
        category=category,
        event_code=event_code.strip().lower(),
        severity=severity,
        points_delta=points_delta,
        status=PerformanceScoringRule.Status.PROPOSED,
        reason=reason.strip(),
        created_by=actor,
    )


@transaction.atomic
def approve_scoring_rule(*, rule_id, actor):
    """Approve a proposed rule; one approved rule may match each category/event-code/severity combination."""
    _require_admin(actor)
    rule = PerformanceScoringRule.objects.select_for_update().get(pk=rule_id)
    if rule.status != PerformanceScoringRule.Status.PROPOSED:
        raise ValidationError({"rule": "Only a proposed rule can be approved."})

    rule.status = PerformanceScoringRule.Status.APPROVED
    rule.approved_by = actor
    rule.approved_at = timezone.now()
    try:
        rule.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
    except IntegrityError as exc:
        raise ValidationError({
            "rule": "An approved rule already exists for this category, event code, and severity. Retire it before approving a replacement."
        }) from exc
    return rule


@transaction.atomic
def retire_scoring_rule(*, rule_id, actor):
    """Retire an approved rule without rewriting applications made under it."""
    _require_admin(actor)
    rule = PerformanceScoringRule.objects.select_for_update().get(pk=rule_id)
    if rule.status != PerformanceScoringRule.Status.APPROVED:
        raise ValidationError({"rule": "Only an approved rule can be retired."})
    rule.status = PerformanceScoringRule.Status.RETIRED
    rule.save(update_fields=["status", "updated_at"])
    return rule
