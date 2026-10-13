import uuid

from django.conf import settings
from django.db import models


class PerformanceEventReview(models.Model):
    """Immutable record of an authorized decision about a reported event."""

    class Decision(models.TextChoices):
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        MORE_EVIDENCE = "more_evidence", "More evidence requested"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        "performance.PerformanceEvent",
        on_delete=models.PROTECT,
        related_name="review_history",
    )
    decision = models.CharField(max_length=20, choices=Decision.choices)
    reason = models.TextField()
    requested_evidence = models.TextField(blank=True)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="performance_event_reviews",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event", "created_at"], name="perf_review_event_time_idx"),
        ]

    def __str__(self):
        return f"{self.event_id}: {self.decision}"
