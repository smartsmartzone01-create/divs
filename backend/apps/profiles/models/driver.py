import uuid

from django.conf import settings
from django.db import models


class DriverProfile(models.Model):
    """Driver's working-system profile, separate from registration and verification."""

    class Status(models.TextChoices):
        PENDING_ACTIVATION = "pending_activation", "Pending activation"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        CLOSED = "closed", "Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    registration = models.OneToOneField(
        "registrations.DriverRegistration",
        on_delete=models.CASCADE,
        related_name="profile",
    )
    status = models.CharField(
        max_length=24,
        choices=Status.choices,
        default=Status.PENDING_ACTIVATION,
    )
    availability_activated_at = models.DateTimeField(null=True, blank=True)
    availability_activated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="activated_driver_profiles",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Driver profile"
        verbose_name_plural = "Driver profiles"

    @property
    def account(self):
        """Resolve the shared account through the registration without duplicating its FK."""
        return self.registration.account

    def __str__(self):
        return f"Driver profile for {self.account.pk}"
