import uuid

from django.conf import settings
from django.db import models


class Notification(models.Model):
    """A private in-app notification for one account in one role workspace."""

    class RecipientRole(models.TextChoices):
        DRIVER = "driver", "Driver"
        CLIENT = "client", "Client"
        OPERATIONS = "operations", "Operations"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    recipient_role = models.CharField(max_length=16, choices=RecipientRole.choices)
    event_type = models.CharField(max_length=64)
    title = models.CharField(max_length=160)
    message = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["recipient", "recipient_role", "created_at"],
                name="notif_rec_role_created_idx",
            ),
            models.Index(
                fields=["recipient", "recipient_role", "read_at"],
                name="notif_rec_role_read_idx",
            ),
        ]

    @property
    def is_read(self):
        return self.read_at is not None

    def __str__(self):
        return f"{self.recipient_id} [{self.recipient_role}] — {self.event_type}"
