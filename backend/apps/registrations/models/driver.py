import uuid

from django.conf import settings
from django.db import models


class DriverRegistration(models.Model):
    """Initial information submitted when an account registers as a driver."""

    class ExperienceLevel(models.TextChoices):
        NONE = "none", "No professional driving experience"
        UNDER_ONE_YEAR = "under_1_year", "Less than 1 year"
        ONE_TO_THREE_YEARS = "1_to_3_years", "1–3 years"
        FOUR_TO_SEVEN_YEARS = "4_to_7_years", "4–7 years"
        EIGHT_PLUS_YEARS = "8_plus_years", "8 or more years"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="driver_registration",
    )
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    nationality = models.CharField(max_length=100)
    region = models.CharField(max_length=120)
    district = models.CharField(max_length=120)
    current_residential_address = models.TextField()
    driving_experience = models.CharField(
        max_length=24,
        choices=ExperienceLevel.choices,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Driver registration"
        verbose_name_plural = "Driver registrations"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.id})"
