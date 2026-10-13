import uuid

from django.conf import settings
from django.db import models


class PerformanceAppeal(models.Model):
    """A driver's challenge to a performance event decision."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        UPHELD = "upheld", "Appeal successful"
        DENIED = "denied", "Appeal unsuccessful"
        WITHDRAWN = "withdrawn", "Withdrawn"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        "performance.PerformanceEvent",
        on_delete=models.PROTECT,
        related_name="appeals",
    )
    appellant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="performance_appeals",
    )
    reason = models.TextField()
    evidence_references = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="decided_performance_appeals",
        null=True,
        blank=True,
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    decision_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["event"],
                condition=models.Q(status="pending"),
                name="perf_one_pending_appeal_event",
            ),
        ]
        indexes = [
            models.Index(fields=["status", "created_at"], name="perf_appeal_status_time_idx"),
        ]

    def __str__(self):
        return f"Appeal for event {self.event_id}: {self.status}"


class PerformanceAppealDecision(models.Model):
    """Historical record of an appeal decision; never overwrite earlier decisions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appeal = models.ForeignKey(
        "performance.PerformanceAppeal",
        on_delete=models.PROTECT,
        related_name="decision_history",
    )
    status = models.CharField(max_length=16, choices=PerformanceAppeal.Status.choices)
    reason = models.TextField()
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="performance_appeal_decisions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["appeal", "created_at"], name="perf_appeal_decision_time_idx"),
        ]

    def __str__(self):
        return f"Appeal {self.appeal_id}: {self.status}"
