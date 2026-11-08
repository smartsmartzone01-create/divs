from datetime import timedelta
from io import StringIO
from uuid import uuid4
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.identity.models import Account
from apps.registrations.models import DriverRegistration
from apps.profiles.models import DriverProfile
from apps.verification.models import (
    DriverVerificationEvidence,
    DriverVerificationEvidenceEvent,
)


@override_settings(
    R2_EVIDENCE_STORAGE_ENABLED=True,
    R2_BUCKET_NAME="divs-private-evidence",
)
class EvidenceRetentionCommandTests(TestCase):
    def setUp(self):
        actor = Account.objects.create_user(
            email="retention-driver@example.com",
            password="StrongPassword123!",
        )
        registration = DriverRegistration.objects.create(
            account=actor,
            first_name="Amani",
            middle_name="",
            last_name="Juma",
            nationality="Tanzanian",
            region="Dar es Salaam",
            district="Kinondoni",
            current_residential_address="Mikocheni",
            driving_experience="1_to_3_years",
        )
        check = DriverProfile.objects.create(registration=registration).verification.checks.first()
        self.eligible = self._evidence(check, legal_hold=False)
        self.held = self._evidence(check, legal_hold=True)
        self.not_expired = self._evidence(
            check,
            status=DriverVerificationEvidence.Status.SUBMITTED,
            legal_hold=False,
        )

    def _evidence(self, check, *, legal_hold, status=DriverVerificationEvidence.Status.EXPIRED):
        return DriverVerificationEvidence.objects.create(
            verification_check=check,
            evidence_type=check.check_type,
            source=DriverVerificationEvidence.Source.DRIVER_UPLOAD,
            status=status,
            scan_status=DriverVerificationEvidence.ScanStatus.CLEAN,
            storage_key=f"verification-evidence/{'held' if legal_hold else status}-{uuid4()}",
            expires_at=timezone.now() - timedelta(days=1),
            legal_hold=legal_hold,
        )

    @patch("apps.verification.management.commands.purge_expired_verification_evidence._s3_client")
    def test_dry_run_does_not_delete_objects_or_change_metadata(self, get_client):
        output = StringIO()
        call_command("purge_expired_verification_evidence", stdout=output)

        get_client.assert_not_called()
        self.eligible.refresh_from_db()
        self.assertTrue(self.eligible.storage_key)
        self.assertIsNone(self.eligible.storage_deleted_at)

    @patch("apps.verification.management.commands.purge_expired_verification_evidence._s3_client")
    def test_execute_deletes_only_expired_files_without_legal_hold(self, get_client):
        output = StringIO()
        call_command("purge_expired_verification_evidence", "--execute", stdout=output)

        get_client.return_value.delete_object.assert_called_once_with(
            Bucket="divs-private-evidence",
            Key=self.eligible.storage_key,
        )
        self.eligible.refresh_from_db()
        self.held.refresh_from_db()
        self.not_expired.refresh_from_db()
        self.assertEqual(self.eligible.storage_key, "")
        self.assertIsNotNone(self.eligible.storage_deleted_at)
        self.assertTrue(self.held.storage_key)
        self.assertTrue(self.not_expired.storage_key)
        self.assertTrue(
            DriverVerificationEvidenceEvent.objects.filter(
                evidence=self.eligible,
                event_type="retention_file_deleted",
            ).exists()
        )

    @override_settings(R2_EVIDENCE_STORAGE_ENABLED=False)
    def test_retention_command_fails_closed_when_storage_is_not_configured(self):
        with self.assertRaises(CommandError):
            call_command("purge_expired_verification_evidence", "--execute")

