import uuid

from django.conf import settings
from django.db import models


class PerformanceScoringRule(models.Model):
    """A versioned score rule; only Admin-approved rules may be applied."""

    class Category(models.TextChoices):
        POSITIVE = "positive", "Positive"
        NEGATIVE = "negative", "Negative"

    class Status(models.TextChoices):
        PROPOSED = "proposed", "Proposed"
        APPROVED = "approved", "Approved"
        RETIRED = "retired", "Retired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=160)
    category = models.CharField(max_length=16, choices=Category.choices)
    event_code = models.CharField(max_length=64)
    severity = models.CharField(
        max_length=16,
        choices=[
            ("", "Not specified"),
            ("minor", "Minor"),
            ("serious", "Serious"),
            ("critical", "Critical"),
        ],
        blank=True,
        default="",
    )
    points_delta = models.SmallIntegerField()
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PROPOSED,
    )
    reason = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_performance_scoring_rules",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="approved_performance_scoring_rules",
        null=True,
        blank=True,
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "severity", "-created_at"]
        indexes = [
            models.Index(fields=["category", "event_code", "severity", "status"], name="perf_rule_lookup_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(points_delta__gte=-100, points_delta__lte=100),
                name="perf_rule_delta_range",
            ),
            models.UniqueConstraint(
                fields=["category", "event_code", "severity"],
                condition=models.Q(status="approved"),
                name="perf_one_approved_rule_match",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.category}/{self.severity}: {self.points_delta:+d})"
