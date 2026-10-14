import uuid

from django.conf import settings
from django.db import models


class DriverVerification(models.Model):
    """Verification decision and progress; never stores government response payloads."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_REVIEW = "in_review", "In review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.OneToOneField("profiles.DriverProfile", on_delete=models.CASCADE, related_name="verification")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="driver_verification_decisions")
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_discoverable(self):
        """Require overall approval and a validated licence with at least one class."""
        licence_check = self.checks.filter(
            check_type=DriverVerificationCheck.CheckType.DRIVING_LICENCE,
            status=DriverVerificationCheck.Status.PASSED,
            result_code=DriverVerificationCheck.ResultCode.VALID,
        ).first()
        successful_results = {
            DriverVerificationCheck.CheckType.NATIONAL_IDENTITY: DriverVerificationCheck.ResultCode.MATCH,
            DriverVerificationCheck.CheckType.DRIVING_LICENCE: DriverVerificationCheck.ResultCode.VALID,
            DriverVerificationCheck.CheckType.TRAFFIC_RECORDS: DriverVerificationCheck.ResultCode.CLEAR,
            DriverVerificationCheck.CheckType.ACCIDENT_RECORDS: DriverVerificationCheck.ResultCode.CLEAR,
        }
        all_checks_successful = all(
            self.checks.filter(
                check_type=check_type,
                status=DriverVerificationCheck.Status.PASSED,
                result_code=result_code,
            ).exists()
            for check_type, result_code in successful_results.items()
        )
        return (
            self.profile.status == "active"
            and self.status == self.Status.APPROVED
            and all_checks_successful
            and licence_check is not None
            and licence_check.verified_licence_classes.filter(is_current=True).exists()
        )

    def __str__(self):
        return f"Driver verification for {self.profile_id} ({self.status})"


class DriverVerificationCheck(models.Model):
    class CheckType(models.TextChoices):
        NATIONAL_IDENTITY = "national_identity", "National identity"
        DRIVING_LICENCE = "driving_licence", "Driving licence"
        TRAFFIC_RECORDS = "traffic_records", "Traffic/police records"
        ACCIDENT_RECORDS = "accident_records", "Accident records"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_REVIEW = "in_review", "In review"
        PASSED = "passed", "Passed"
        FAILED = "failed", "Failed"
        NEEDS_REVIEW = "needs_review", "Needs review"
        UNAVAILABLE = "unavailable", "Source unavailable"

    class Method(models.TextChoices):
        GOVERNMENT_API = "government_api", "Government API"
        MANUAL = "manual", "Manual review"

    class ResultCode(models.TextChoices):
        MATCH = "match", "Information matched"
        MISMATCH = "mismatch", "Information mismatch"
        VALID = "valid", "Valid"
        INVALID = "invalid", "Invalid"
        CLEAR = "clear", "No disqualifying record reported"
        RECORD_FOUND = "record_found", "Record requires review"
        INCONCLUSIVE = "inconclusive", "Inconclusive"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    verification = models.ForeignKey(DriverVerification, on_delete=models.CASCADE, related_name="checks")
    check_type = models.CharField(max_length=32, choices=CheckType.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    method = models.CharField(max_length=20, choices=Method.choices, blank=True)
    result_code = models.CharField(max_length=24, choices=ResultCode.choices, blank=True)
    checked_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_driver_verification_checks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["check_type"]
        constraints = [models.UniqueConstraint(fields=["verification", "check_type"], name="uniq_driver_verification_check")]
        indexes = [models.Index(fields=["status", "check_type"], name="drv_vcheck_status_type_idx")]

    def __str__(self):
        return f"{self.check_type} — {self.status}"


class VerifiedDriverLicenceClass(models.Model):
    """A licence class confirmed during validation of the driver's presented licence."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    licence_check = models.ForeignKey(DriverVerificationCheck, on_delete=models.PROTECT, related_name="verified_licence_classes")
    licence_class = models.CharField(max_length=12)
    is_current = models.BooleanField(default=True)
    verified_at = models.DateTimeField()
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="verified_driver_licence_classes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["licence_class"]
        constraints = [models.UniqueConstraint(fields=["licence_check", "licence_class"], name="uniq_verified_licence_class_per_check")]
        indexes = [models.Index(fields=["licence_class", "is_current"], name="verified_lic_class_current_idx")]

    @property
    def qualifies_for_discovery(self):
        return (
            self.is_current
            and self.licence_check.check_type == DriverVerificationCheck.CheckType.DRIVING_LICENCE
            and self.licence_check.status == DriverVerificationCheck.Status.PASSED
            and self.licence_check.result_code == DriverVerificationCheck.ResultCode.VALID
        )

    def __str__(self):
        return f"{self.licence_class} ({self.licence_check.verification.profile_id})"
