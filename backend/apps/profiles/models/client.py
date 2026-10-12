import uuid

from django.db import models


class ClientProfile(models.Model):
    """Client's working-system profile, separate from client registration."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        CLOSED = "closed", "Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    registration = models.OneToOneField(
        "registrations.ClientRegistration",
        on_delete=models.CASCADE,
        related_name="profile",
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Client profile"
        verbose_name_plural = "Client profiles"

    @property
    def account(self):
        """Resolve the shared account through the registration without duplicating its FK."""
        return self.registration.account

    def __str__(self):
        return f"Client profile for {self.account_id}"
