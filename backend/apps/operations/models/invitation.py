import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class OperationsInvitation(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        OPERATOR = "operator", "Operator"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=254, db_index=True)
    role = models.CharField(max_length=16, choices=Role.choices)
    code_hash = models.CharField(max_length=128)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sent_operations_invitations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email", "created_at"], name="ops_inv_email_created_idx"),
        ]

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    @property
    def is_usable(self):
        now = timezone.now()
        return (
            self.revoked_at is None
            and self.used_at is None
            and (self.expires_at is None or now < self.expires_at)
        )

    def __str__(self):
        return f"{self.role} invitation for {self.email}"
