import uuid

from django.conf import settings
from django.db import models


class OperationsMembership(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        OPERATOR = "operator", "Operator"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="operations_membership",
    )
    role = models.CharField(max_length=16, choices=Role.choices)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="approved_operations_memberships",
    )
    approved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-approved_at"]

    def __str__(self):
        return f"{self.account} — {self.role}"
