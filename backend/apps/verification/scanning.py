from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.module_loading import import_string

from apps.verification.storage import _s3_client, _validate_evidence_storage_key
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



def scan_verification_evidence(*, evidence_id):
    """
    Fetch a quarantined object and pass its bytes to the configured scanner adapter.

    Adapter contract:
      - provider_name: stable, non-sensitive provider identifier (max 80 chars)
      - scan(content, content_type=..., filename=...): returns "clean" or "infected"

    No scanner configured, provider failure, malformed output, or storage failure
    must never result in a clean state.
    """
    scanner_path = settings.DIVS_EVIDENCE_SCANNER_CLASS
    if not scanner_path:
        raise EvidenceScanError(
            "No trusted evidence scanner is configured; the file remains quarantined."
        )

    evidence = DriverVerificationEvidence.objects.filter(pk=evidence_id).first()
    if evidence is None:
        raise EvidenceScanError("Evidence record not found.")
    if evidence.storage_deleted_at is not None or not evidence.storage_key:
        raise EvidenceScanError("The evidence file is no longer available for scanning.")
    if evidence.status == DriverVerificationEvidence.Status.EXPIRED:
        raise EvidenceScanError("Expired evidence cannot be scanned.")

    try:
        scanner_class = import_string(scanner_path)
        scanner = scanner_class()
        provider = str(getattr(scanner, "provider_name", "") or "").strip()
        if not provider or len(provider) > 80:
            raise EvidenceScanError("The configured scanner has no valid provider identifier.")

        _validate_evidence_storage_key(evidence.storage_key)
        client = _s3_client()
        result = client.get_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=evidence.storage_key,
        )
        body = result["Body"]
        try:
            content = body.read(settings.R2_MAX_UPLOAD_BYTES + 1)
        finally:
            body.close()

        if len(content) != evidence.file_size or len(content) > settings.R2_MAX_UPLOAD_BYTES:
            raise EvidenceScanError("The stored evidence size does not match its metadata.")

        outcome = scanner.scan(
            content,
            content_type=evidence.content_type,
            filename=evidence.original_filename,
        )
        if outcome not in {
            DriverVerificationEvidence.ScanStatus.CLEAN,
            DriverVerificationEvidence.ScanStatus.INFECTED,
        }:
            outcome = DriverVerificationEvidence.ScanStatus.ERROR
    except EvidenceScanError:
        raise
    except Exception:
        provider = locals().get("provider", "scanner-unavailable")
        if len(provider) > 80:
            provider = "scanner-unavailable"
        return record_evidence_scan_result(
            evidence_id=evidence_id,
            outcome=DriverVerificationEvidence.ScanStatus.ERROR,
            provider=provider,
        )

    return record_evidence_scan_result(
        evidence_id=evidence_id,
        outcome=outcome,
        provider=provider,
    )
