import uuid

from django.db import models


class DriverScore(models.Model):
    """Current calculated score state for an existing driver profile.

    A null score is intentional until the baseline eligibility policy is finalized
    and the driver's applicable history has been reviewed. It is not a score of 0.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver = models.OneToOneField(
        "profiles.DriverProfile",
        on_delete=models.PROTECT,
        related_name="performance_score",
    )
    calculated_score = models.PositiveSmallIntegerField(null=True, blank=True)
    calculation_updated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Driver performance score"
        verbose_name_plural = "Driver performance scores"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(calculated_score__isnull=True)
                | models.Q(calculated_score__gte=0, calculated_score__lte=100),
                name="performance_score_between_0_and_100",
            ),
        ]

    def __str__(self):
        score = "not yet established" if self.calculated_score is None else str(self.calculated_score)
        return f"Performance score for driver {self.driver_id}: {score}"
