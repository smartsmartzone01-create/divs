import uuid

from django.conf import settings
from django.db import models


class PerformanceEvent(models.Model):
    """A reported performance event; reports do not affect scores until approved."""

    class Category(models.TextChoices):
        POSITIVE = "positive", "Positive"
        NEGATIVE = "negative", "Negative"
        CORRECTION = "correction", "Correction"

    class Severity(models.TextChoices):
        MINOR = "minor", "Minor"
        SERIOUS = "serious", "Serious"
        CRITICAL = "critical", "Critical"

    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under review"
        MORE_EVIDENCE = "more_evidence", "More evidence requested"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    class SourceType(models.TextChoices):
        OPERATIONS = "operations", "Operations entry"
        CLIENT = "client", "Client submission"
        TRUSTED_INTEGRATION = "trusted_integration", "Trusted integration"
        OTHER = "other", "Other authorized source"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver = models.ForeignKey(
        "profiles.DriverProfile",
        on_delete=models.PROTECT,
        related_name="performance_events",
    )
    category = models.CharField(max_length=16, choices=Category.choices)
    # Stable event type used to select a specific approved scoring rule.
    event_code = models.CharField(max_length=64, blank=True, default="")
    severity = models.CharField(max_length=16, choices=Severity.choices, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    occurred_at = models.DateTimeField(null=True, blank=True)
    source_type = models.CharField(max_length=24, choices=SourceType.choices, default=SourceType.OPERATIONS)
    source_reference = models.CharField(max_length=160, blank=True)
    # Optional idempotency key supplied by a trusted source to help prevent duplicate reports.
    idempotency_key = models.CharField(max_length=160, null=True, blank=True, unique=True)
    # Store references/metadata only; do not place raw government records or sensitive payloads here.
    evidence_references = models.JSONField(default=list, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submitted_performance_events",
        null=True,
        blank=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reviewed_performance_events",
        null=True,
        blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    decision_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["driver", "status"], name="performance_driver_status_idx"),
            models.Index(fields=["category", "status"], name="perf_event_cat_status_idx"),
        ]

    def __str__(self):
        return f"{self.get_category_display()}: {self.title} ({self.status})"
