import uuid

from django.conf import settings
from django.db import models


class ClientRegistration(models.Model):
    """Contact and location details for an individual or company client."""

    class ClientType(models.TextChoices):
        INDIVIDUAL = "individual", "Individual"
        COMPANY = "company", "Company"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_registration",
    )
    client_type = models.CharField(max_length=16, choices=ClientType.choices)
    name = models.CharField(max_length=200)
    primary_contact = models.CharField(max_length=40)
    email = models.EmailField(max_length=254)
    country = models.CharField(max_length=100)
    region = models.CharField(max_length=120)
    alternative_contacts = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Client registration"
        verbose_name_plural = "Client registrations"

    def __str__(self):
        return f"{self.name} ({self.client_type})"
