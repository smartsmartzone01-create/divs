import uuid

from django.db import models


class OperationsProfile(models.Model):
    """Profile for an operations member after their application is approved."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        CLOSED = "closed", "Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    membership = models.OneToOneField(
        "operations.OperationsMembership",
        on_delete=models.CASCADE,
        related_name="profile",
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Operations profile"
        verbose_name_plural = "Operations profiles"

    @property
    def account(self):
        """Resolve the shared account through the approved membership."""
        return self.membership.account

    def __str__(self):
        return f"Operations profile for {self.account_id}"
