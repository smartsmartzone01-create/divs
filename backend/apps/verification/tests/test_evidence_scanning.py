from django.test import TestCase

from apps.identity.models import Account
from apps.registrations.models import DriverRegistration
from apps.profiles.models import DriverProfile
from apps.verification.models import (
    DriverVerificationEvidence,
    DriverVerificationEvidenceEvent,
)
from apps.verification.scanning import EvidenceScanError, record_evidence_scan_result


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
