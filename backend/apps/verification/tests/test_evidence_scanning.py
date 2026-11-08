import io
from unittest.mock import patch

from django.test import TestCase, override_settings

from apps.identity.models import Account
from apps.registrations.models import DriverRegistration
from apps.profiles.models import DriverProfile
from apps.verification.models import (
    DriverVerificationEvidence,
    DriverVerificationEvidenceEvent,
)
from apps.verification.scanning import (
    EvidenceScanError,
    record_evidence_scan_result,
    scan_verification_evidence,
)


class CleanTestScanner:
    provider_name = "test-scanner"

    def scan(self, content, *, content_type, filename):
        if content != b"test":
            raise ValueError("Unexpected test payload")
        return DriverVerificationEvidence.ScanStatus.CLEAN


class FailingTestScanner:
    provider_name = "test-scanner"

    def scan(self, content, *, content_type, filename):
        raise RuntimeError("scanner unavailable")


class EvidenceScanningServiceTests(TestCase):
    def setUp(self):
        self.actor = Account.objects.create_user(
            email="scan-driver@example.com",
            password="StrongPassword123!",
        )
        registration = DriverRegistration.objects.create(
            account=self.actor,
            first_name="Amani",
            middle_name="",
            last_name="Juma",
            nationality="Tanzanian",
            region="Dar es Salaam",
            district="Kinondoni",
            current_residential_address="Mikocheni",
            driving_experience="1_to_3_years",
        )
        profile = DriverProfile.objects.create(registration=registration)
        check = profile.verification.checks.first()
        self.evidence = DriverVerificationEvidence.objects.create(
            verification_check=check,
            evidence_type=check.check_type,
            source=DriverVerificationEvidence.Source.DRIVER_UPLOAD,
            storage_key="verification-evidence/test-object",
            original_filename="identity.jpg",
            content_type="image/jpeg",
            file_size=4,
        )

    def test_clean_scan_result_is_recorded_with_audit_event(self):
        evidence = record_evidence_scan_result(
            evidence_id=self.evidence.id,
            outcome=DriverVerificationEvidence.ScanStatus.CLEAN,
            provider="configured-scanner",
        )

        self.assertEqual(evidence.scan_status, DriverVerificationEvidence.ScanStatus.CLEAN)
        self.assertEqual(evidence.scan_provider, "configured-scanner")
        self.assertIsNotNone(evidence.scanned_at)
        self.assertTrue(
            DriverVerificationEvidenceEvent.objects.filter(
                evidence=evidence,
                event_type="security_scan_completed",
                previous_status=DriverVerificationEvidence.ScanStatus.PENDING,
                new_status=DriverVerificationEvidence.ScanStatus.CLEAN,
            ).exists()
        )

    def test_infected_result_remains_a_distinct_non_clean_state(self):
        evidence = record_evidence_scan_result(
            evidence_id=self.evidence.id,
            outcome=DriverVerificationEvidence.ScanStatus.INFECTED,
            provider="configured-scanner",
        )
        self.assertEqual(evidence.scan_status, DriverVerificationEvidence.ScanStatus.INFECTED)

    def test_unknown_or_missing_provider_cannot_mark_evidence_clean(self):
        for provider in ("", " "):
            with self.subTest(provider=provider):
                with self.assertRaises(EvidenceScanError):
                    record_evidence_scan_result(
                        evidence_id=self.evidence.id,
                        outcome=DriverVerificationEvidence.ScanStatus.CLEAN,
                        provider=provider,
                    )

        with self.assertRaises(EvidenceScanError):
            record_evidence_scan_result(
                evidence_id=self.evidence.id,
                outcome=DriverVerificationEvidence.ScanStatus.PENDING,
                provider="configured-scanner",
            )

        self.evidence.refresh_from_db()
        self.assertEqual(self.evidence.scan_status, DriverVerificationEvidence.ScanStatus.PENDING)


    @override_settings(
        DIVS_EVIDENCE_SCANNER_CLASS="apps.verification.tests.test_evidence_scanning.CleanTestScanner",
        R2_EVIDENCE_STORAGE_ENABLED=True,
        R2_BUCKET_NAME="divs-private-evidence",
        R2_MAX_UPLOAD_BYTES=10 * 1024 * 1024,
    )
    @patch("apps.verification.scanning._s3_client")
    def test_configured_scanner_reads_quarantined_object_and_records_clean(self, get_client):
        get_client.return_value.get_object.return_value = {"Body": io.BytesIO(b"test")}

        evidence = scan_verification_evidence(evidence_id=self.evidence.id)

        self.assertEqual(evidence.scan_status, DriverVerificationEvidence.ScanStatus.CLEAN)
        self.assertEqual(evidence.scan_provider, "test-scanner")
        get_client.return_value.get_object.assert_called_once_with(
            Bucket="divs-private-evidence",
            Key="verification-evidence/test-object",
        )

    @override_settings(DIVS_EVIDENCE_SCANNER_CLASS="")
    @patch("apps.verification.scanning._s3_client")
    def test_missing_scanner_keeps_evidence_quarantined(self, get_client):
        with self.assertRaises(EvidenceScanError):
            scan_verification_evidence(evidence_id=self.evidence.id)

        get_client.assert_not_called()
        self.evidence.refresh_from_db()
        self.assertEqual(self.evidence.scan_status, DriverVerificationEvidence.ScanStatus.PENDING)

    @override_settings(
        DIVS_EVIDENCE_SCANNER_CLASS="apps.verification.tests.test_evidence_scanning.FailingTestScanner",
        R2_EVIDENCE_STORAGE_ENABLED=True,
        R2_BUCKET_NAME="divs-private-evidence",
        R2_MAX_UPLOAD_BYTES=10 * 1024 * 1024,
    )
    @patch("apps.verification.scanning._s3_client")
    def test_scanner_failure_records_error_and_never_clean(self, get_client):
        get_client.return_value.get_object.return_value = {"Body": io.BytesIO(b"test")}

        evidence = scan_verification_evidence(evidence_id=self.evidence.id)

        self.assertEqual(evidence.scan_status, DriverVerificationEvidence.ScanStatus.ERROR)
        self.assertEqual(evidence.scan_provider, "test-scanner")
