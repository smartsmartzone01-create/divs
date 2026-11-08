from django.test import TestCase

from apps.identity.models import Account
from apps.registrations.models import DriverRegistration
from apps.profiles.models import DriverProfile
from apps.verification.models import (
    DriverVerificationCheck,
    DriverVerificationEvidence,
    DriverVerificationEvidenceEvent,
)
from apps.verification.serializers import DriverVerificationSerializer


class DriverVerificationEvidenceTests(TestCase):
    def test_evidence_metadata_and_history_are_serialized_without_private_storage_fields(self):
        driver = Account.objects.create_user(
            email="evidence-driver@example.com",
            password="StrongPassword123!",
        )
        registration = DriverRegistration.objects.create(
            account=driver,
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
        verification = profile.verification
        check = verification.checks.get(
            check_type=DriverVerificationCheck.CheckType.NATIONAL_IDENTITY
        )
        evidence = DriverVerificationEvidence.objects.create(
            verification_check=check,
            evidence_type=check.check_type,
            source=DriverVerificationEvidence.Source.PHYSICAL_INSPECTION,
            status=DriverVerificationEvidence.Status.UNDER_REVIEW,
            original_filename="identity-document.jpg",
            content_type="image/jpeg",
            file_size=2048,
            storage_key="private/evidence/example",
            sha256="a" * 64,
        )
        DriverVerificationEvidenceEvent.objects.create(
            evidence=evidence,
            event_type="submitted",
            new_status=DriverVerificationEvidence.Status.UNDER_REVIEW,
        )

        data = DriverVerificationSerializer(verification).data
        evidence_data = data["checks"][0]["evidence"][0]

        self.assertEqual(evidence_data["source"], "physical_inspection")
        self.assertEqual(evidence_data["status"], "under_review")
        self.assertEqual(len(evidence_data["events"]), 1)
        self.assertNotIn("storage_key", evidence_data)
        self.assertNotIn("sha256", evidence_data)
        self.assertNotIn("source_reference", evidence_data)
