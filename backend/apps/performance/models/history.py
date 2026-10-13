import uuid

from django.conf import settings
from django.db import models


class ScoreHistory(models.Model):
    """Append-only record of a score decision or change.

    Normal application workflows should create new rows rather than edit or delete
    prior history. This model keeps the score transition separate from the current
    score state stored on DriverScore.
    """

    class ChangeType(models.TextChoices):
        BASELINE = "baseline", "Baseline established"
        EVENT = "event", "Approved performance event"
        MANUAL_OVERRIDE = "manual_override", "Admin manual override"
        CORRECTION = "correction", "Correction"
        RECALCULATION = "recalculation", "Recalculation"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    score = models.ForeignKey(
        "performance.DriverScore",
        on_delete=models.PROTECT,
        related_name="history_entries",
    )
    event = models.ForeignKey(
        "performance.PerformanceEvent",
        on_delete=models.PROTECT,
        related_name="score_history_entries",
        null=True,
        blank=True,
    )
    change_type = models.CharField(max_length=24, choices=ChangeType.choices)
    previous_score = models.PositiveSmallIntegerField(null=True, blank=True)
    new_score = models.PositiveSmallIntegerField()
    reason = models.TextField()
    rule_reference = models.CharField(max_length=120, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="performance_score_history_actions",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["score", "created_at"], name="perf_score_history_time_idx"),
            models.Index(fields=["event", "created_at"], name="perf_event_history_time_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(new_score__gte=0, new_score__lte=100),
                name="perf_history_new_score_range",
            ),
            models.CheckConstraint(
                condition=models.Q(previous_score__isnull=True)
                | models.Q(previous_score__gte=0, previous_score__lte=100),
                name="perf_history_previous_score_range",
            ),
        ]

    @property
    def change_amount(self):
        """Return the signed change; a baseline has no previous score."""
        if self.previous_score is None:
            return None
        return self.new_score - self.previous_score

    def __str__(self):
        return f"{self.change_type}: {self.previous_score} -> {self.new_score}"
