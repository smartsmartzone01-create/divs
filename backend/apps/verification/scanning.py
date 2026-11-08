from django.db import transaction
from django.utils import timezone

from apps.verification.models import (
    DriverVerificationEvidence,
    DriverVerificationEvidenceEvent,
)


class EvidenceScanError(Exception):
    """Raised when a security scan result cannot be safely recorded."""


@transaction.atomic
def record_evidence_scan_result(*, evidence_id, outcome, provider):
    """
    Record a result from a trusted, internal scanner integration.

    This function deliberately has no public API endpoint. The caller must be
    a trusted backend worker/integration; user-supplied scan results are never
    accepted. A missing scanner must leave evidence quarantined.
    """
    allowed_outcomes = {
        DriverVerificationEvidence.ScanStatus.CLEAN,
        DriverVerificationEvidence.ScanStatus.INFECTED,
        DriverVerificationEvidence.ScanStatus.ERROR,
    }
    provider = str(provider or "").strip()
    if outcome not in allowed_outcomes:
        raise EvidenceScanError("Unsupported evidence scan outcome.")
    if not provider or len(provider) > 80:
        raise EvidenceScanError("A valid scanner provider identifier is required.")

    evidence = (
        DriverVerificationEvidence.objects.select_for_update()
        .filter(pk=evidence_id)
        .first()
    )
    if evidence is None:
        raise EvidenceScanError("Evidence record not found.")

    previous_status = evidence.scan_status
    evidence.scan_status = outcome
    evidence.scan_provider = provider
    evidence.scanned_at = timezone.now()
    evidence.save(update_fields=["scan_status", "scan_provider", "scanned_at", "updated_at"])

    DriverVerificationEvidenceEvent.objects.create(
        evidence=evidence,
        event_type="security_scan_completed",
        previous_status=previous_status,
        new_status=outcome,
        notes=f"Scanner: {provider}",
    )
    return evidence
