import uuid

from django.conf import settings
from django.db import models


class AvailabilityRestriction(models.Model):
    """A performance-related restriction separate from profile/verification status."""

    class Kind(models.TextChoices):
        CRITICAL_INCIDENT = "critical_incident", "Critical incident review"
        LOW_SCORE = "low_score", "Low performance score"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        RELEASED = "released", "Released"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver = models.ForeignKey(
        "profiles.DriverProfile",
        on_delete=models.PROTECT,
        related_name="availability_restrictions",
    )
    kind = models.CharField(max_length=24, choices=Kind.choices)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    reason = models.TextField()
    source_event = models.ForeignKey(
        "performance.PerformanceEvent",
        on_delete=models.PROTECT,
        related_name="availability_restrictions",
        null=True,
        blank=True,
    )
    source_score = models.ForeignKey(
        "performance.DriverScore",
        on_delete=models.PROTECT,
        related_name="availability_restrictions",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_availability_restrictions",
        null=True,
        blank=True,
    )
    released_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="released_availability_restrictions",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)
    release_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["driver", "status"], name="perf_restrict_driver_status_idx"),
            models.Index(fields=["kind", "status"], name="perf_restrict_kind_status_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["source_event", "kind"],
                condition=models.Q(status="active", source_event__isnull=False),
                name="perf_one_active_event_restriction",
            ),
        ]

    def __str__(self):
        return f"{self.driver_id}: {self.kind} ({self.status})"


class AvailabilityRestrictionDecision(models.Model):
    """Append-only audit history for restriction placement and release decisions."""

    class Action(models.TextChoices):
        PLACED = "placed", "Restriction placed"
        RELEASED = "released", "Restriction released"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restriction = models.ForeignKey(
        "performance.AvailabilityRestriction",
        on_delete=models.PROTECT,
        related_name="decision_history",
    )
    action = models.CharField(max_length=12, choices=Action.choices)
    reason = models.TextField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="availability_restriction_decisions",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["restriction", "created_at"], name="perf_restrict_decision_time_idx"),
        ]

    def __str__(self):
        return f"{self.restriction_id}: {self.action}"
