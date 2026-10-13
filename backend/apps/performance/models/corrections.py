import uuid

from django.conf import settings
from django.db import models


class PerformanceScoreCorrection(models.Model):
    """Audit record for an upheld appeal and its score recalculation outcome."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appeal = models.OneToOneField(
        "performance.PerformanceAppeal",
        on_delete=models.PROTECT,
        related_name="score_correction",
    )
    event = models.ForeignKey(
        "performance.PerformanceEvent",
        on_delete=models.PROTECT,
        related_name="score_corrections",
    )
    score = models.ForeignKey(
        "performance.DriverScore",
        on_delete=models.PROTECT,
        related_name="corrections",
        null=True,
        blank=True,
    )
    previous_calculated_score = models.PositiveSmallIntegerField(null=True, blank=True)
    new_calculated_score = models.PositiveSmallIntegerField(null=True, blank=True)
    removed_points_delta = models.SmallIntegerField(null=True, blank=True)
    reason = models.TextField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="performance_score_corrections",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["score", "created_at"], name="perf_correction_score_time_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(previous_calculated_score__isnull=True)
                | models.Q(previous_calculated_score__gte=0, previous_calculated_score__lte=100),
                name="perf_correction_previous_range",
            ),
            models.CheckConstraint(
                condition=models.Q(new_calculated_score__isnull=True)
                | models.Q(new_calculated_score__gte=0, new_calculated_score__lte=100),
                name="perf_correction_new_range",
            ),
        ]

    def __str__(self):
        return f"Correction for appeal {self.appeal_id}"
