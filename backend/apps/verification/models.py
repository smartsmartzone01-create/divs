import uuid

from django.conf import settings
from django.db import models


class DriverVerification(models.Model):
    """Verification progress and final decision; never stores government response payloads."""

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
    decision_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def checks_are_complete(self):
        required_types = {value for value, _label in DriverVerificationCheck.CheckType.choices}
        checks = list(self.checks.all())
        expected_results = {
            DriverVerificationCheck.CheckType.NATIONAL_IDENTITY: DriverVerificationCheck.ResultCode.MATCH,
            DriverVerificationCheck.CheckType.DRIVING_LICENCE: DriverVerificationCheck.ResultCode.VALID,
            DriverVerificationCheck.CheckType.TRAFFIC_RECORDS: DriverVerificationCheck.ResultCode.CLEAR,
            DriverVerificationCheck.CheckType.ACCIDENT_RECORDS: DriverVerificationCheck.ResultCode.CLEAR,
        }
        allowed_scan_statuses = [DriverVerificationEvidence.ScanStatus.CLEAN]
        if settings.DEBUG and getattr(settings, "DIVS_ALLOW_UNSCANNED_EVIDENCE_ACCESS", False):
            allowed_scan_statuses.append(DriverVerificationEvidence.ScanStatus.PENDING)

        def has_accepted_manual_evidence(check):
            if check.method != DriverVerificationCheck.Method.MANUAL:
                return True
            return check.evidence.filter(
                status=DriverVerificationEvidence.Status.ACCEPTED,
                scan_status__in=allowed_scan_statuses,
                storage_deleted_at__isnull=True,
                storage_key__gt="",
                evidence_type=check.check_type,
            ).exists()

        return (
            {check.check_type for check in checks} == required_types
            and all(
                check.status == DriverVerificationCheck.Status.PASSED
                and check.result_code == expected_results.get(check.check_type)
                and has_accepted_manual_evidence(check)
                for check in checks
            )
        )

    @property
    def is_discoverable(self):
        """Require final approval, Admin activation, all successful checks and a current licence class."""
        successful_results = {
            DriverVerificationCheck.CheckType.NATIONAL_IDENTITY: DriverVerificationCheck.ResultCode.MATCH,
            DriverVerificationCheck.CheckType.DRIVING_LICENCE: DriverVerificationCheck.ResultCode.VALID,
            DriverVerificationCheck.CheckType.TRAFFIC_RECORDS: DriverVerificationCheck.ResultCode.CLEAR,
            DriverVerificationCheck.CheckType.ACCIDENT_RECORDS: DriverVerificationCheck.ResultCode.CLEAR,
        }
        checks_by_type = {check.check_type: check for check in self.checks.all()}
        for check_type, result_code in successful_results.items():
            check = checks_by_type.get(check_type)
            if (
                check is None
                or check.status != DriverVerificationCheck.Status.PASSED
                or check.result_code != result_code
            ):
                return False
            if check.method == DriverVerificationCheck.Method.MANUAL:
                allowed_scan_statuses = [DriverVerificationEvidence.ScanStatus.CLEAN]
                if settings.DEBUG and getattr(settings, "DIVS_ALLOW_UNSCANNED_EVIDENCE_ACCESS", False):
                    allowed_scan_statuses.append(DriverVerificationEvidence.ScanStatus.PENDING)
                if not check.evidence.filter(
                    status=DriverVerificationEvidence.Status.ACCEPTED,
                    scan_status__in=allowed_scan_statuses,
                    storage_deleted_at__isnull=True,
                    storage_key__gt="",
                    evidence_type=check.check_type,
                ).exists():
                    return False

        licence_check = checks_by_type.get(DriverVerificationCheck.CheckType.DRIVING_LICENCE)
        has_current_class = (
            licence_check is not None
            and any(item.is_current for item in licence_check.verified_licence_classes.all())
        )
        return (
            self.profile.status == "active"
            and self.status == self.Status.APPROVED
            and has_current_class
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
    review_notes = models.TextField(blank=True)
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


class DriverVerificationEvent(models.Model):
    """Append-only audit trail for verification findings and administrative decisions."""

    class EventType(models.TextChoices):
        CHECK_REVIEWED = "check_reviewed", "Check reviewed"
        GOVERNMENT_API_RESULT = "government_api_result", "Government API result recorded"
        APPROVED = "approved", "Verification approved"
        REJECTED = "rejected", "Verification rejected"
        AVAILABILITY_ACTIVATED = "availability_activated", "Availability activated"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    verification = models.ForeignKey(DriverVerification, on_delete=models.CASCADE, related_name="events")
    verification_check = models.ForeignKey(DriverVerificationCheck, on_delete=models.SET_NULL, null=True, blank=True, related_name="events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="driver_verification_events")
    event_type = models.CharField(max_length=32, choices=EventType.choices)
    previous_status = models.CharField(max_length=16, blank=True)
    new_status = models.CharField(max_length=24, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]



class GovernmentVerificationAttempt(models.Model):
    """Minimal audit metadata for a trusted government verification request.

    Government source payloads and identity/licence/police records are never stored.
    """
    class Outcome(models.TextChoices):
        MATCHED = "matched", "Matched / valid / clear"
        NOT_MATCHED = "not_matched", "Mismatch / invalid / record found"
        INCONCLUSIVE = "inconclusive", "Inconclusive"
        UNAVAILABLE = "unavailable", "Source unavailable"
        ERROR = "error", "Integration error"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    verification_check = models.ForeignKey(
        DriverVerificationCheck,
        on_delete=models.PROTECT,
        related_name="government_attempts",
    )
    provider = models.CharField(max_length=80)
    provider_reference = models.CharField(max_length=255)
    outcome = models.CharField(max_length=16, choices=Outcome.choices)
    result_code = models.CharField(max_length=24, blank=True)
    response_fingerprint = models.CharField(max_length=64, blank=True)
    completed_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-completed_at"]
        indexes = [
            models.Index(fields=["verification_check", "completed_at"], name="gov_attempt_check_time_idx"),
        ]


class DriverVerificationEvidence(models.Model):
    """Evidence metadata for a check; private file storage is configured separately."""

    class Source(models.TextChoices):
        DRIVER_UPLOAD = "driver_upload", "Driver upload"
        OPERATIONS_UPLOAD = "operations_upload", "Operations upload"
        PHYSICAL_INSPECTION = "physical_inspection", "Physical inspection"
        GOVERNMENT_API = "government_api", "Government API"

    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under review"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        EXPIRED = "expired", "Expired"
        SUPERSEDED = "superseded", "Superseded"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    verification_check = models.ForeignKey(
        DriverVerificationCheck,
        on_delete=models.PROTECT,
        related_name="evidence",
    )
    evidence_type = models.CharField(
        max_length=32,
        choices=DriverVerificationCheck.CheckType.choices,
    )
    source = models.CharField(max_length=24, choices=Source.choices)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.SUBMITTED,
    )

    class ScanStatus(models.TextChoices):
        PENDING = "pending", "Quarantined / scan pending"
        CLEAN = "clean", "Scan clean"
        INFECTED = "infected", "Threat detected"
        ERROR = "error", "Scan failed"

    scan_status = models.CharField(
        max_length=12,
        choices=ScanStatus.choices,
        default=ScanStatus.PENDING,
    )
    scan_provider = models.CharField(max_length=80, blank=True)
    scanned_at = models.DateTimeField(null=True, blank=True)
    legal_hold = models.BooleanField(default=False)
    storage_deleted_at = models.DateTimeField(null=True, blank=True)
    original_filename = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=120, blank=True)
    file_size = models.PositiveBigIntegerField(null=True, blank=True)
    sha256 = models.CharField(max_length=64, blank=True)
    storage_key = models.CharField(max_length=512, blank=True)
    source_reference = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_driver_verification_evidence",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_driver_verification_evidence",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-submitted_at"]
        indexes = [
            models.Index(fields=["verification_check", "status"], name="drv_evidence_check_status_idx"),
            models.Index(fields=["evidence_type", "source"], name="drv_evidence_type_source_idx"),
        ]

    def __str__(self):
        return f"{self.evidence_type} evidence ({self.status})"


class DriverVerificationEvidenceEvent(models.Model):
    """Append-only audit history for evidence review and lifecycle changes."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evidence = models.ForeignKey(
        DriverVerificationEvidence,
        on_delete=models.PROTECT,
        related_name="events",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="driver_verification_evidence_events",
    )
    event_type = models.CharField(max_length=32)
    previous_status = models.CharField(max_length=16, blank=True)
    new_status = models.CharField(max_length=16, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

