import uuid

from django.db import models


class PerformanceEventScoreApplication(models.Model):
    """Immutable record of a scoring rule applied to one approved event."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.OneToOneField(
        "performance.PerformanceEvent",
        on_delete=models.PROTECT,
        related_name="score_application",
    )
    score = models.ForeignKey(
        "performance.DriverScore",
        on_delete=models.PROTECT,
        related_name="event_applications",
    )
    rule = models.ForeignKey(
        "performance.PerformanceScoringRule",
        on_delete=models.PROTECT,
        related_name="applications",
    )
    rule_name_snapshot = models.CharField(max_length=160)
    points_delta = models.SmallIntegerField()
    previous_score = models.PositiveSmallIntegerField()
    new_score = models.PositiveSmallIntegerField()
    reason = models.TextField()
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-applied_at"]
        indexes = [
            models.Index(fields=["score", "applied_at"], name="perf_app_score_time_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(previous_score__gte=0, previous_score__lte=100),
                name="perf_application_previous_range",
            ),
            models.CheckConstraint(
                condition=models.Q(new_score__gte=0, new_score__lte=100),
                name="perf_application_new_range",
            ),
        ]

    @property
    def applied_change(self):
        return self.new_score - self.previous_score

    def __str__(self):
        return f"{self.event_id}: {self.previous_score} -> {self.new_score}"
